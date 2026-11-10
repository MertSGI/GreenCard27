"""Deep Biometric Photo and Passport Scan Validation Engine for GreenCard27.

Evaluates uploaded documents against US Department of State (Bureau of Consular Affairs)
Diversity Visa and Immigrant Visa technical specifications:
- Exact 600x600 px (or 1200x1200 px) 1:1 square dimensions
- True JPEG / JFIF 24-bit sRGB color space (rejection of Grayscale, CMYK, Palette)
- Strict <= 240 KB file size limits
- Background luminance, uniformity, and color cast analysis
- Exposure, overexposure, and contrast testing
- Passport scan resolution (>=600px) and file size (<=5MB) verification
"""
from __future__ import annotations

import io
from typing import Dict, Any, List, Tuple
from PIL import Image, ImageStat


def validate_biometric_photo(file_bytes: bytes, filename: str = "photo.jpg") -> Dict[str, Any]:
    """Perform comprehensive technical and quality checks on a biometric photo."""
    checks: List[Tuple[str, bool, str]] = []
    warnings: List[str] = []
    fname = filename.lower()
    size_bytes = len(file_bytes)
    size_kb = size_bytes / 1024.0

    if fname.endswith(".pdf"):
        return {
            "valid": False,
            "checks": [("Dosya Formatı", False, "PDF formatı tespit edildi.")],
            "warnings": ["PDF dosyaları ABD Dışişleri Bakanlığı sistemi tarafından kabul edilmez."],
            "formatted_report": (
                "❌ *HATA: PDF Formatı Kabul Edilmez!*\n\n"
                "ABD Dışişleri Bakanlığı kurallarına göre biyometrik fotoğraflar *kesinlikle JPEG (.jpg / .jpeg)* formatında olmalıdır.\n"
                "👉 Lütfen fotoğrafınızı JPEG olarak kaydedip tekrar gönderin."
            ),
        }

    try:
        bio = io.BytesIO(file_bytes)
        img = Image.open(bio)
        width, height = img.size
        img_format = (img.format or "").upper()
        mode = img.mode
    except Exception as exc:
        return {
            "valid": False,
            "checks": [("Görüntü Okuma", False, f"Bozuk dosya: {exc}")],
            "warnings": ["Gönderdiğiniz dosya geçerli bir fotoğraf olarak okunamadı."],
            "formatted_report": f"⚠️ Gönderilen dosya görüntü olarak açılamadı ({exc}). Lütfen standart bir JPEG fotoğrafı gönderin.",
        }

    # 1. Format Kontrolü (JPEG / JFIF)
    is_jpeg = img_format in ("JPEG", "JPG", "JFIF")
    checks.append((
        "JPEG/JFIF Formatı",
        is_jpeg,
        f"Mevcut Format: {img_format} ({'Kabul Edildi' if is_jpeg else 'JPEG olmalı'})"
    ))

    # 2. Boyut Kontrolü (600x600 veya 1200x1200 px)
    is_600 = (width == 600 and height == 600)
    is_1200 = (width == 1200 and height == 1200)
    is_square = (width == height)
    is_exact_dim = is_600 or is_1200
    dim_msg = f"{width}x{height} px"
    if is_600:
        dim_msg += " (Standart 600x600 piksel ✅)"
    elif is_1200:
        dim_msg += " (Yüksek Çözünürlük 1200x1200 piksel ✅)"
    else:
        dim_msg += " (Tam olarak 600x600 veya 1200x1200 piksel kare olmalıdır ❌)"
    checks.append(("600x600 Piksel Kare Çözünürlük", is_exact_dim, dim_msg))

    # 3. Dosya Boyutu Kontrolü (<= 240 KB)
    is_size_ok = (size_kb <= 240.0)
    checks.append((
        "Dosya Boyutu (<= 240 KB)",
        is_size_ok,
        f"{size_kb:.1f} KB ({'Uygun' if is_size_ok else 'Maksimum 240 KB olmalıdır'})"
    ))

    # 4. Renk Modu Kontrolü (24-bit sRGB)
    is_rgb = (mode == "RGB")
    color_msg = f"Renk Alanı: {mode}"
    if is_rgb:
        color_msg += " (24-bit Renkli sRGB ✅)"
    elif mode in ("L", "1"):
        color_msg += " (Siyah-Beyaz / Gri Tonlama Kabul Edilmez! ❌)"
    elif mode == "CMYK":
        color_msg += " (Baskı CMYK modu; web sRGB olmalıdır ❌)"
    else:
        color_msg += " (RGB moduna dönüştürülmelidir ❌)"
    checks.append(("Renkli Fotoğraf (RGB)", is_rgb, color_msg))

    # 5. Arka Plan Aydınlık & Renk Analizi (Background Luminance & Uniformity)
    # Köşe ve üst kenar piksellerinden arka plan örneği alıyoruz
    try:
        rgb_img = img.convert("RGB")
        w_sample = min(width, 40)
        h_sample = min(height, 40)
        # Sol üst köşe ve sağ üst köşe
        tl_box = rgb_img.crop((0, 0, w_sample, h_sample))
        tr_box = rgb_img.crop((width - w_sample, 0, width, h_sample))
        
        stat_tl = ImageStat.Stat(tl_box)
        stat_tr = ImageStat.Stat(tr_box)
        
        # Ortalama parlaklık (luminance)
        mean_r = (stat_tl.mean[0] + stat_tr.mean[0]) / 2.0
        mean_g = (stat_tl.mean[1] + stat_tr.mean[1]) / 2.0
        mean_b = (stat_tl.mean[2] + stat_tr.mean[2]) / 2.0
        bg_luminance = 0.299 * mean_r + 0.587 * mean_g + 0.114 * mean_b
        
        # Doygunluk (Saturation) - Renkli arka plan tespiti (mavi, kırmızı duvar vb.)
        max_c = max(mean_r, mean_g, mean_b)
        min_c = min(mean_r, mean_g, mean_b)
        bg_saturation = (max_c - min_c) / max(1.0, max_c)

        if bg_luminance < 185:
            warnings.append(
                f"Arka plan yeterince beyaz veya açık görünmüyor (Aydınlık skoru: {bg_luminance:.0f}/255). "
                "Gri, gölgeli veya koyu arka planlar ABD konsolosluğu sisteminde elenme sebebidir."
            )
        elif bg_saturation > 0.18:
            warnings.append(
                "Arka planda belirgin bir renk tonu tespit edildi. "
                "Arka plan düz beyaz veya kırık beyaz olmalıdır."
            )
    except Exception:
        bg_luminance = 200

    # 6. Genel Pozlama ve Kontrast Kontrolü
    try:
        overall_stat = ImageStat.Stat(img.convert("L"))
        overall_mean = overall_stat.mean[0]
        if overall_mean < 70:
            warnings.append("Fotoğraf genel olarak çok karanlık / az pozlanmış görünüyor.")
        elif overall_mean > 230:
            warnings.append("Fotoğraf aşırı aydınlık / parlamış (yüz detayları kaybolabilir).")
    except Exception:
        pass

    all_critical_ok = is_jpeg and is_exact_dim and is_size_ok and is_rgb

    # Markdown Raporu İnşası
    lines = ["📸 *Biyometrik Fotoğraf Teknik Analiz Raporu*", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for label, passed, detail in checks:
        icon = "✅" if passed else "❌"
        lines.append(f"{icon} *{label}:* {detail}")

    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    if all_critical_ok:
        lines.append("🎉 *TEKNİK UYGUNLUK: GEÇTİ (TAM UYUMLU)*\nFotoğrafınız ABD Dışişleri Bakanlığı piksel, format ve boyut kriterlerini eksiksiz karşılıyor.")
        if warnings:
            lines.append("\n⚠️ *Kalite ve Görsel Uyarılar:*")
            for w in warnings:
                lines.append(f"• {w}")
        lines.append(
            "\n👁️ *Son Manuel Kontroller:* Gözlük takılmamalı, doğrudan kameraya bakılmalı, doğal tebessüm/nötr ifade olmalı ve fotoğraf son 6 ayda çekilmiş olmalıdır."
        )
    else:
        lines.append("🛠️ *DÜZELTİLMESİ GEREKEN TEKNİK EKSİKLİKLER:*")
        for label, passed, detail in checks:
            if not passed:
                lines.append(f"• *{label}:* {detail}")
        if warnings:
            for w in warnings:
                lines.append(f"• {w}")
        lines.append(
            "\n💡 *Nasıl Düzeltilir?*\n"
            "Fotoğrafınızı [ABD Dışişleri Resmi Photo Tool](https://tsg.phototool.state.gov/photo) "
            "aracına yükleyerek otomatik olarak 600x600 piksele kırpabilir ve buraya tekrar gönderebilirsiniz."
        )

    return {
        "valid": all_critical_ok,
        "is_jpeg": is_jpeg,
        "is_exact_dim": is_exact_dim,
        "is_size_ok": is_size_ok,
        "is_rgb": is_rgb,
        "checks": checks,
        "warnings": warnings,
        "formatted_report": "\n".join(lines),
    }


def validate_passport_scan(file_bytes: bytes, filename: str = "passport.jpg") -> Dict[str, Any]:
    """Perform checks on a passport biometric and signature page scan."""
    checks: List[Tuple[str, bool, str]] = []
    fname = filename.lower()
    size_bytes = len(file_bytes)
    size_kb = size_bytes / 1024.0
    size_mb = size_kb / 1024.0

    if fname.endswith(".pdf"):
        return {
            "valid": False,
            "formatted_report": (
                "❌ *HATA: PDF Formatı Kabul Edilmez!*\n\n"
                "ABD Dışişleri Bakanlığı kurallarına göre pasaport kimlik ve imza sayfası taraması "
                "*kesinlikle JPEG (.jpg / .jpeg)* olmalıdır. PDF dosyaları reddedilir."
            ),
        }

    try:
        bio = io.BytesIO(file_bytes)
        img = Image.open(bio)
        width, height = img.size
        img_format = (img.format or "").upper()
    except Exception as exc:
        return {
            "valid": False,
            "formatted_report": f"⚠️ Dosya görüntü olarak açılamadı ({exc}). Lütfen JPEG formatında gönderin.",
        }

    is_jpeg = img_format in ("JPEG", "JPG", "JFIF")
    checks.append((
        "JPEG/JFIF Formatı (PDF Değil)",
        is_jpeg,
        f"Format: {img_format} ({'Uygun' if is_jpeg else 'JPEG olmalı'})",
    ))

    is_size_ok = (size_mb <= 5.0)
    checks.append((
        "Dosya Boyutu (<= 5 MB)",
        is_size_ok,
        f"{size_mb:.2f} MB ({'Uygun' if is_size_ok else 'Maksimum 5 MB olmalı'})",
    ))

    is_res_ok = (width >= 600 and height >= 600)
    checks.append((
        "Okunabilir Çözünürlük (>= 600 px)",
        is_res_ok,
        f"{width}x{height} px ({'Okunabilir' if is_res_ok else 'Çözünürlük çok düşük'})",
    ))

    all_ok = is_jpeg and is_size_ok and is_res_ok

    lines = ["🛂 *Pasaport Kimlik & İmza Sayfası Tarama Kontrolü*", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
    for label, passed, detail in checks:
        icon = "✅" if passed else "❌"
        lines.append(f"{icon} *{label}:* {detail}")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    if all_ok:
        lines.append(
            "🎉 *Harika!* Pasaport taramanız yükleme kriterlerine uygun ve okunabilir kalitede.\n"
            "⚠️ Pasaportunuzun fotoğraflı kimlik sayfası ile imza sayfasının birlikte ve parlamasız göründüğünden emin olun."
        )
    else:
        lines.append(
            "⚠️ Taramanız kriterleri tam karşılamıyor. Lütfen JPEG formatında ve net çözünürlükte tekrar taratıp gönderin."
        )

    return {
        "valid": all_ok,
        "checks": checks,
        "formatted_report": "\n".join(lines),
    }
