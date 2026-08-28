"""Foundry Local bağlantısı (SDK 1.2.4).

SDK, modelle doğrudan yerel interop üzerinden konuşur — ayrı bir HTTP sunucusu
ya da OpenAI istemcisi gerekmez. Yine de istek/yanıt şekilleri OpenAI ile
uyumludur, bu yüzden mesaj sözlükleri aynı biçimdedir.

Modeller ilk kullanımda indirilir (internet gerekir); sonrası tamamen offline.
"""

from __future__ import annotations

from typing import Callable, Sequence

from . import config


class FoundryClient:
    """chat + embedding modellerini yerelde hazırlar ve çağırır."""

    def __init__(
        self,
        chat_alias: str | None = None,
        embed_alias: str | None = None,
        progress: Callable[[str], None] | None = None,
    ) -> None:
        self._say = progress or (lambda _msg: None)
        self.chat_alias = chat_alias or config.CHAT_MODEL_ALIAS
        self.embed_alias = embed_alias or config.EMBED_MODEL_ALIAS

        self._manager = _manager()
        _ensure_execution_providers(self._manager, self._say)

        self._chat_model = self._prepare(self.chat_alias)
        self._embed_model = self._prepare(self.embed_alias)

        self.chat_model_id = self._chat_model.id
        self.embed_model_id = self._embed_model.id

        self._chat_client = self._chat_model.get_chat_client()
        self._chat_client.settings.temperature = config.CHAT_TEMPERATURE
        self._chat_client.settings.max_tokens = config.CHAT_MAX_TOKENS

        self._embed_client = self._embed_model.get_embedding_client()

    # -- hazırlık ---------------------------------------------------------

    def _prepare(self, alias: str):
        model = self._manager.catalog.get_model(alias)
        if model is None:
            raise RuntimeError(
                f"Model bulunamadı: {alias!r}. Kataloğu görmek için: foundry model list"
            )

        if not model.is_cached:
            self._say(f"  {alias} indiriliyor ({model.id})...")
            son = -10.0

            def ilerleme(yuzde: float) -> None:
                nonlocal son
                if yuzde - son >= 10.0 or yuzde >= 100.0:
                    son = yuzde
                    self._say(f"    {alias}: %{yuzde:.0f}")

            model.download(progress_callback=ilerleme)

        if not model.is_loaded:
            self._say(f"  {alias} belleğe yükleniyor...")
            model.load()
        return model

    # -- kullanım ---------------------------------------------------------

    def embed(self, texts: Sequence[str]) -> list[list[float]]:
        """Metinleri vektöre çevir. Çıktı sırası girdi sırasıyla aynıdır."""
        if not texts:
            return []
        response = self._embed_client.generate_embeddings(list(texts))
        # Sıraya güvenmek yerine index'e göre diziyoruz; sağlayıcı sırayı bozarsa
        # chunk'lar yanlış vektörle eşleşir ve bu sessizce yanlış cevap üretir.
        ordered = sorted(response.data, key=lambda item: item.index)
        if len(ordered) != len(texts):
            raise RuntimeError(
                f"Embedding sayısı girdiyle uyuşmuyor: {len(ordered)} != {len(texts)}"
            )
        return [list(item.embedding) for item in ordered]

    def embed_one(self, text: str) -> list[float]:
        return self.embed([text])[0]

    def chat(self, messages: list[dict[str, str]]) -> str:
        completion = self._chat_client.complete_chat(messages)
        if not completion.choices:
            raise RuntimeError("Model boş yanıt döndürdü (choices yok)")
        return (completion.choices[0].message.content or "").strip()

    def unload(self) -> None:
        """Modelleri bellekten düşür."""
        for model in (self._chat_model, self._embed_model):
            try:
                if model.is_loaded:
                    model.unload()
            except Exception:  # pragma: no cover - kapanışta hata yutulur
                pass


def _manager():
    """Tekil (singleton) manager'ı döndür.

    SDK manager'ı singleton'dır: ikinci kez kurmaya çalışmak hata verir.
    Testlerde birden çok istemci oluşturulabildiği için mevcut örnek yeniden
    kullanılır.
    """
    from foundry_local_sdk import Configuration, FoundryLocalManager

    if FoundryLocalManager.instance is None:
        FoundryLocalManager.initialize(Configuration(app_name=config.APP_NAME))
    return FoundryLocalManager.instance


def _ensure_execution_providers(manager, say: Callable[[str], None]) -> None:
    """Donanım hızlandırıcılarını (CUDA/WebGPU) bu uygulama adına kaydet.

    Kayıt YAPILMAZSA SDK sessizce CPU varyantını seçer ve her şey çalışmaya
    devam eder — sadece kat kat yavaş. Bu sessiz düşüşü engellemek için kayıt
    her açılışta yapılır.

    Kayıt durumu SÜREÇ BAŞINADIR: her yeni çalıştırmada `is_registered` yine
    False döner. Ancak EP dosyaları bir kez indirildikten sonra kayıt saniyeler
    sürer; uzun süren yalnızca ilk indirmedir.
    """
    try:
        eksik = [ep.name for ep in manager.discover_eps() if not ep.is_registered]
    except Exception as exc:  # pragma: no cover - EP keşfi başarısızsa CPU ile devam
        say(f"  (uyarı) hızlandırıcı durumu okunamadı, CPU ile devam: {exc}")
        return

    if not eksik:
        return

    say(f"  Hızlandırıcılar hazırlanıyor: {', '.join(eksik)}")
    say("    (ilk çalıştırmada indirme birkaç dakika sürer, sonrakilerde saniyeler)")
    bildirilen: set[tuple[str, int]] = set()

    def ilerleme(ad: str, yuzde: float) -> None:
        adim = int(yuzde // 25) * 25
        if (ad, adim) not in bildirilen:
            bildirilen.add((ad, adim))
            say(f"    {ad}: %{adim}")

    try:
        sonuc = manager.download_and_register_eps(progress_callback=ilerleme)
    except Exception as exc:  # pragma: no cover
        say(f"  (uyarı) hızlandırıcı kaydı başarısız, CPU ile devam: {exc}")
        return

    if sonuc.failed_eps:
        say(f"  (uyarı) kaydedilemeyen hızlandırıcılar: {sonuc.failed_eps}")
