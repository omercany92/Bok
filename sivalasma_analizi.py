#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sıvılaşma Analizi Programı
Yöntem: Seed & Idriss (1971) Basitleştirilmiş Yöntem (Yilmaz vd. güncellemeleriyle)
SPT tabanlı sıvılaşma potansiyeli değerlendirmesi
"""

import math
import sys


def veri_girisi():
    """Kullanıcıdan gerekli verileri alır."""
    print("=" * 65)
    print("        SIVILAŞMA ANALİZİ PROGRAMI")
    print("   (Seed & Idriss Basitleştirilmiş Yöntemi - SPT Tabanlı)")
    print("=" * 65)

    print("\n--- DEPREM VERİLERİ ---")
    Mw = float(input("Deprem büyüklüğü (Mw)                    : "))
    amax = float(input("Maksimum yer ivmesi (amax, g cinsinden)   : "))

    print("\n--- ZEMİN PROFİLİ VERİLERİ ---")
    n = int(input("Analiz yapılacak tabaka sayısı             : "))

    tabakalar = []
    for i in range(n):
        print(f"\n  >> Tabaka {i + 1} <<")
        derinlik = float(input(f"  Tabaka orta noktası derinliği (m)        : "))
        gamma = float(input(f"  Zemin birim hacim ağırlığı (kN/m³)       : "))
        N_spt = int(input(f"  SPT-N darbe sayısı                       : "))
        ince_dane = float(input(f"  İnce dane oranı FC (%)                   : "))

        tabakalar.append({
            "derinlik": derinlik,
            "gamma": gamma,
            "N_spt": N_spt,
            "ince_dane": ince_dane,
        })

    print("\n--- YERALTI SUYU ---")
    yw_derinlik = float(input("Yeraltı su seviyesi derinliği (m)          : "))

    return Mw, amax, tabakalar, yw_derinlik


def duzeltilmis_spt(N_spt, sigma_v_efektif):
    """SPT-N değerini düzeltir (N1)60 hesaplar."""
    if sigma_v_efektif <= 0:
        CN = 1.0
    else:
        CN = min(1.7, math.sqrt(100.0 / sigma_v_efektif))

    # Diğer düzeltme katsayıları standart varsayımlar
    CE = 1.0   # Enerji oranı düzeltmesi (varsayılan %60 enerji)
    CB = 1.0   # Kuyu çapı düzeltmesi
    CR = 1.0   # Çubuk boyu düzeltmesi
    CS = 1.0   # Numune alıcı düzeltmesi

    N1_60 = N_spt * CN * CE * CB * CR * CS
    return round(N1_60, 1)


def ince_dane_duzeltmesi(N1_60, FC):
    """İnce dane oranına göre (N1)60cs hesaplar (Youd vd. 2001)."""
    if FC <= 5:
        alpha = 0.0
        beta = 1.0
    elif FC < 35:
        alpha = math.exp(1.76 - (190.0 / (FC ** 2)))
        beta = 0.99 + (FC ** 1.5 / 1000.0)
    else:
        alpha = 5.0
        beta = 1.2

    N1_60cs = alpha + beta * N1_60
    return round(N1_60cs, 1)


def hesapla_CRR(N1_60cs):
    """Düzeltilmiş SPT değerine göre CRR7.5 hesaplar (Youd vd. 2001)."""
    if N1_60cs >= 30:
        return None  # Sıvılaşmayan zemin

    CRR_75 = (1.0 / (34.0 - N1_60cs)
              + (N1_60cs / 135.0)
              + (50.0 / (10.0 * N1_60cs + 45.0) ** 2)
              - 1.0 / 200.0)
    return round(CRR_75, 4)


def buyukluk_olcek_faktoru(Mw):
    """Deprem büyüklüğü ölçek faktörü (MSF) hesaplar."""
    MSF = 10.0 ** (2.24) / (Mw ** 2.56)
    return round(MSF, 3)


def hesapla_rd(derinlik):
    """Gerilme azaltma katsayısı (rd) hesaplar (Liao & Whitman, 1986)."""
    if derinlik <= 9.15:
        rd = 1.0 - 0.00765 * derinlik
    elif derinlik <= 23.0:
        rd = 1.174 - 0.0267 * derinlik
    else:
        rd = 0.744 - 0.008 * derinlik
        rd = max(rd, 0.1)
    return round(rd, 4)


def hesapla_CSR(sigma_v, sigma_v_eff, amax, rd):
    """Tekrarlı gerilme oranı (CSR) hesaplar."""
    if sigma_v_eff <= 0:
        return 0
    CSR = 0.65 * (sigma_v / sigma_v_eff) * amax * rd
    return round(CSR, 4)


def gerilme_hesapla(tabakalar, yw_derinlik):
    """Her tabaka için toplam ve efektif gerilmeleri hesaplar."""
    gamma_su = 9.81  # kN/m³

    for t in tabakalar:
        z = t["derinlik"]
        sigma_v = t["gamma"] * z  # Toplam düşey gerilme (basitleştirilmiş)

        if z <= yw_derinlik:
            u = 0
        else:
            u = gamma_su * (z - yw_derinlik)

        sigma_v_eff = sigma_v - u

        t["sigma_v"] = round(sigma_v, 2)
        t["sigma_v_eff"] = round(sigma_v_eff, 2)
        t["u"] = round(u, 2)


def analiz_yap(Mw, amax, tabakalar, yw_derinlik):
    """Tüm tabakalar için sıvılaşma analizini gerçekleştirir."""
    gerilme_hesapla(tabakalar, yw_derinlik)
    MSF = buyukluk_olcek_faktoru(Mw)

    for t in tabakalar:
        z = t["derinlik"]

        # Su seviyesi üstündeki tabakalar sıvılaşmaz
        if z <= yw_derinlik:
            t["durum"] = "Su seviyesi üstü - Sıvılaşma riski yok"
            t["FS"] = None
            t["CSR"] = None
            t["CRR"] = None
            t["N1_60"] = None
            t["N1_60cs"] = None
            continue

        # SPT düzeltmeleri
        N1_60 = duzeltilmis_spt(t["N_spt"], t["sigma_v_eff"])
        N1_60cs = ince_dane_duzeltmesi(N1_60, t["ince_dane"])
        t["N1_60"] = N1_60
        t["N1_60cs"] = N1_60cs

        # CSR hesabı
        rd = hesapla_rd(z)
        CSR = hesapla_CSR(t["sigma_v"], t["sigma_v_eff"], amax, rd)
        t["CSR"] = CSR
        t["rd"] = rd

        # CRR hesabı
        CRR_75 = hesapla_CRR(N1_60cs)
        if CRR_75 is None:
            t["CRR"] = None
            t["FS"] = None
            t["durum"] = "Sıvılaşmayan zemin ((N1)60cs ≥ 30)"
            continue

        CRR = CRR_75 * MSF
        t["CRR"] = round(CRR, 4)

        # Güvenlik sayısı
        if CSR > 0:
            FS = CRR / CSR
        else:
            FS = 999
        t["FS"] = round(FS, 2)

        # Durum değerlendirmesi
        if FS < 1.0:
            t["durum"] = "SIVILAŞMA RİSKİ VAR"
        elif FS < 1.25:
            t["durum"] = "Sınırda - Dikkatli olunmalı"
        else:
            t["durum"] = "Güvenli - Sıvılaşma beklenmez"

    return MSF


def sonuclari_yazdir(Mw, amax, tabakalar, yw_derinlik, MSF):
    """Analiz sonuçlarını ekrana yazdırır."""
    print("\n")
    print("=" * 65)
    print("               ANALİZ SONUÇLARI")
    print("=" * 65)

    print(f"\n  Deprem Büyüklüğü (Mw)         : {Mw}")
    print(f"  Maks. Yer İvmesi (amax)       : {amax}g")
    print(f"  Yeraltı Su Seviyesi           : {yw_derinlik} m")
    print(f"  Büyüklük Ölçek Faktörü (MSF)  : {MSF}")

    print("\n" + "-" * 65)
    print(f"{'Tabaka':^8}{'z(m)':^7}{'N-SPT':^7}{'(N1)60':^8}"
          f"{'(N1)60cs':^9}{'CSR':^8}{'CRR':^8}{'FS':^7}{'Durum':^20}")
    print("-" * 65)

    for i, t in enumerate(tabakalar):
        z = t["derinlik"]
        n_spt = t["N_spt"]
        n1_60 = t.get("N1_60", "-")
        n1_60cs = t.get("N1_60cs", "-")
        csr = t.get("CSR", "-")
        crr = t.get("CRR", "-")
        fs = t.get("FS", "-")

        n1_60_str = f"{n1_60}" if n1_60 is not None and n1_60 != "-" else "-"
        n1_60cs_str = f"{n1_60cs}" if n1_60cs is not None and n1_60cs != "-" else "-"
        csr_str = f"{csr:.4f}" if isinstance(csr, (int, float)) else "-"
        crr_str = f"{crr:.4f}" if isinstance(crr, (int, float)) else "-"
        fs_str = f"{fs:.2f}" if isinstance(fs, (int, float)) else "-"

        print(f"{i + 1:^8}{z:^7.1f}{n_spt:^7}{n1_60_str:^8}"
              f"{n1_60cs_str:^9}{csr_str:^8}{crr_str:^8}{fs_str:^7}")

    print("-" * 65)

    # Yorumlama
    print("\n" + "=" * 65)
    print("               YORUMLAMA VE DEĞERLENDİRME")
    print("=" * 65)

    sivilan_var = False
    sinirda_var = False

    for i, t in enumerate(tabakalar):
        print(f"\n  Tabaka {i + 1} (z = {t['derinlik']} m):")
        print(f"    Durum: {t['durum']}")

        if t.get("FS") is not None:
            fs = t["FS"]
            if fs < 1.0:
                sivilan_var = True
                print(f"    >> Güvenlik Sayısı FS = {fs:.2f} < 1.0")
                print(f"    >> Bu derinlikte sıvılaşma OLASI.")
                if fs < 0.5:
                    print(f"    >> FS çok düşük! Ciddi sıvılaşma riski mevcut.")
                    print(f"    >> Zemin iyileştirmesi kesinlikle önerilir.")
                elif fs < 0.75:
                    print(f"    >> Orta-yüksek sıvılaşma riski.")
                    print(f"    >> Zemin iyileştirmesi önerilir.")
                else:
                    print(f"    >> Düşük-orta sıvılaşma riski.")
                    print(f"    >> Detaylı analiz önerilir.")
            elif fs < 1.25:
                sinirda_var = True
                print(f"    >> Güvenlik Sayısı FS = {fs:.2f} (1.0 - 1.25 arası)")
                print(f"    >> Sınır durumda, ileri analiz gerekli.")
            else:
                print(f"    >> Güvenlik Sayısı FS = {fs:.2f} ≥ 1.25")
                print(f"    >> Sıvılaşma beklenmez.")

    # Genel değerlendirme
    print("\n" + "=" * 65)
    print("               GENEL DEĞERLENDİRME")
    print("=" * 65)

    if sivilan_var:
        print("""
  [!] UYARI: Zemin profilinde SIVILAŞMA RİSKİ tespit edilmiştir.

  Öneriler:
  1. Detaylı zemin etüdü ve laboratuvar deneyleri yapılmalıdır.
  2. CPT tabanlı analiz ile sonuçlar doğrulanmalıdır.
  3. Zemin iyileştirme yöntemleri değerlendirilmelidir:
     - Vibro-kompaksiyon
     - Jet grout
     - Taş kolon
     - Derin karıştırma
  4. Yapı temel sistemi sıvılaşma etkilerine göre tasarlanmalıdır.
  5. Sıvılaşma sonrası oturma ve yanal yayılma analizleri yapılmalıdır.
""")
    elif sinirda_var:
        print("""
  [~] DİKKAT: Bazı tabakalarda sınır durum tespit edilmiştir.

  Öneriler:
  1. CPT tabanlı analiz ile doğrulama yapılmalıdır.
  2. Olasılıksal sıvılaşma analizi düşünülmelidir.
  3. Tasarımda muhafazakâr yaklaşım benimsenmelidir.
""")
    else:
        print("""
  [✓] Zemin profili sıvılaşma açısından GÜVENLİ görünmektedir.

  Not: Bu sonuç yalnızca girilen veriler için geçerlidir.
  Farklı deprem senaryoları için analizin tekrarlanması önerilir.
""")

    print("=" * 65)
    print("  Not: Bu analiz Seed & Idriss basitleştirilmiş yöntemi ile")
    print("  yapılmıştır. Kesin mühendislik kararları için kapsamlı bir")
    print("  zemin etüdü ve ileri düzey analizler gereklidir.")
    print("=" * 65)


def main():
    try:
        Mw, amax, tabakalar, yw_derinlik = veri_girisi()
        MSF = analiz_yap(Mw, amax, tabakalar, yw_derinlik)
        sonuclari_yazdir(Mw, amax, tabakalar, yw_derinlik, MSF)
    except ValueError:
        print("\n[HATA] Geçersiz veri girişi. Lütfen sayısal değerler giriniz.")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n\nProgram kullanıcı tarafından sonlandırıldı.")
        sys.exit(0)


if __name__ == "__main__":
    main()
