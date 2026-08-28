# Bulut Bilişim — Hafta 7 Ders Notu

## Sanallaştırma Katmanları

Tip-1 hipervizör donanım üzerinde doğrudan çalışır (ESXi, Hyper-V). Yönetim
katmanı işletim sistemine ihtiyaç duymadığı için gecikme düşüktür ve veri
merkezlerinde tercih edilir.

Tip-2 hipervizör bir konak işletim sistemi üzerinde çalışır (VirtualBox,
VMware Workstation). Kurulumu kolaydır ancak konak işletim sisteminin
maliyetini de taşır.

## Konteyner ile Sanal Makine Farkı

Konteynerler konak çekirdeğini paylaşır, sanal makineler kendi çekirdeğini
taşır. Bu yüzden bir konteyner saniyeler içinde, bir sanal makine dakikalar
içinde ayağa kalkar.

Konteyner izolasyonu çekirdek düzeyinde namespace ve cgroup ile sağlanır;
sanal makine izolasyonu ise donanım düzeyindedir ve daha güçlüdür.

## Ders Bilgileri

Final sınavı 14 Ocak 2027 Perşembe günü saat 13:30'da B-204 numaralı
derslikte yapılacaktır. Sınavda tek sayfa el yazısı not bulundurulmasına
izin verilir, basılı kaynak yasaktır.

Dönem projesinin teslimi final sınavından bir hafta önce, 7 Ocak 2027
tarihinde saat 23:59'da sona erer. Geç teslim her gün için 10 puan düşürür.
