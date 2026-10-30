# Hamzeh Crypto Radar — رادار کریپتوی حمزه

**مرجع پروژه:** [مستند جامع فارسی](docs/PROJECT_SPEC_FA.md) · [معماری و فرمول‌ها](docs/TECHNICAL.md) · [وضعیت اجرا، نقص‌ها و ادامه کار](docs/STATUS.md)

**وب‌داشبورد:** https://nimania.github.io/crypto/  
**مخزن:** https://github.com/nimania/crypto

## هدف تأییدشده

دستیار پژوهشی و تصمیم‌گیری حمزه اشرفی برای کشف خودکار فرصت‌های جدید و درحال‌رشد، ارزیابی ورود، پایش سبد و تشخیص کاهش شتاب روند برای بررسی خروج. تحلیل روزانه **و** هفتگی با هم، و اندازه‌گیری همبستگی هر کوین با بیت‌کوین مقدم بر ارزیابی موقعیت است. سامانه نباید سقف بازار یا سود را تضمین کند.

- شبکه‌ها: **Base, Arbitrum, Flare, Ethereum, Solana**. BNB Chain به انتخاب کاربر خارج از محدوده است.
- کیف‌پول اصلی: **MetaMask**؛ Uniswap یکی از پروتکل‌های قابل اتصال است، نه کیف‌پول اصلی.
- دو سبک: معاملات روزانه و نگهداری بلندمدت؛ دو نوع فرصت: بسیار جدید و پروژه‌های در حال رشد.
- خروج بر اساس افت مومنتوم/شیب، نه قیمت سود ثابت؛ فروش کامل یا پله‌ای هر دو قابل بررسی.
- کانال اصلی: **همین وب‌سایت GitHub Pages**؛ **هیچ وابستگی به تلگرام وجود ندارد**.
- هزینه بریج در مدل اصلی انتخاب فرصت اولویت ندارد، مطابق خواست صریح حمزه.
- رمز، seed phrase یا کلید خصوصی وارد پروژه نمی‌شود؛ معاملات خودکار وجود ندارند.

## وضعیت واقعی (نه آرزوهای محصول)

**Experimental / read-only.** اسکن عمومی استخرها، فیلتر مقدماتی، همبستگی آماری BTC، بررسی محدود امنیت EVM، برآورد فرضی اثر قیمت و داشبورد وجود دارند. این موارد **هنوز جایگزین** امنیت قرارداد تأییدشده، sell simulation واقعی، quote اجرایی، پایش عملی سبد MetaMask، بک‌تست معتبر یا موتور پایدار ساختار هفتگی BTC نشده‌اند. پوشش هر پنج شبکه و محدودیت API باید مجدداً در اجرای واقعی تأیید شود. به [وضعیت و موارد باز](docs/STATUS.md) رجوع کنید.

## اجرای محلی

Python 3.11+؛ وابستگی خارجی پایتون در کد فعلی لازم نیست:

```bash
python -m unittest discover -s tests -v
python radar.py
```

خروجی‌ها: `output/radar.json` و `output/report.md`. صفحه `index.html` این JSON را از GitHub Pages می‌خواند.

## استقرار

`.github/workflows/radar.yml` اسکن و انتشار Pages را هر ساعت (UTC: دقیقه ۲۱) یا دستی اجرا می‌کند. GitHub → Settings → Pages → Source: **GitHub Actions**. دکمه «تازه‌سازی» وب‌سایت اسکن جدید آغاز نمی‌کند، فقط آخرین JSON منتشرشده را بازخوانی می‌کند.

## هنگام ادامه پروژه

**اول** [PROJECT_SPEC_FA.md](docs/PROJECT_SPEC_FA.md) را به‌عنوان تصمیم‌های ثبت‌شده کاربر بخوانید، **دوم** [TECHNICAL.md](docs/TECHNICAL.md) را با کد واقعی تطبیق دهید، **سوم** [STATUS.md](docs/STATUS.md) را برای خطاها و کارهای باز بخوانید. هر تغییر معماری/نیاز باید هم‌زمان در مستندات ثبت شود.

> **هشدار:** امتیاز فعلی فقط فعالیت استخر است، نه احتمال رشد یا توصیه خرید/فروش. کمبود داده، خطای API یا شبیه‌سازی ناقص نباید «امن» یا «فرصت وجود ندارد» گزارش شود.

## رادار آربیتراژ ایران (آزمایشی)

صفحه مستقل: [arbitrage.html](https://nimania.github.io/crypto/arbitrage.html). گردآورنده `arbitrage_scan.py` از ابزار read-only `ic_arbitrage` در `iran-crypto-mcp` استفاده می‌کند؛ workflow هم‌زمان با اسکن ساعتی اصلی، `output/arbitrage.json` را منتشر می‌کند. هر خطا یا تغییر فرمت منبع به وضعیت ناقص/ناموجود تبدیل می‌شود، نه ادعای نبود فرصت. نمایش اختلاف خام به معنی سود قابل تحقق نیست؛ کارمزد، برداشت، تأخیر، عمق و لغزش قیمت جداگانه باید کنترل شوند. این نسخه هیچ سفارش یا انتقالی انجام نمی‌دهد. وضعیت اجرا و صحت خروجی زنده هنوز تأیید نشده است.

### اعتبارسنجی مرحله دوم آربیتراژ (آزمایشی)

اسکن ساعتی برای **پنج اختلاف خام بزرگ‌تر** تلاش می‌کند دفتر سفارش خرید و فروش را با سرمایه فرضی ۱۰ میلیون تومان بررسی کند و در صورت امکان کارمزدهای گزارش‌شده را ثبت کند. داده‌های جدید در فیلد `verification` هر فرصت از `arbitrage.json` قرار می‌گیرند. وضعیت `estimated_before_transfer` صرفاً **برآورد قبل از انتقال** است؛ هزینه برداشت، اسلیپیج پس از ثبت سفارش، کارمزدهای اختصاصی کاربر، محدودیت حساب، واریز واقعی و تأخیر بازار در آن تأیید نشده‌اند. برای کارگزارهای بدون دفتر سفارش معتبر، `book_status=unavailable` ثبت می‌شود. هیچ معامله یا انتقالی اجرا نمی‌شود. موفقیت عملیاتی این تغییرات تا اجرای جدید Actions تأیید نشده است.

## Arbitrage Intelligence V2 — experimental (2026-10-30)

- `arbitrage-detail.html` provides per-pair static scenario calculations for user-provided fees and transfer costs, plus observed spread timestamps. It does **not** provide validated net executable profit, and does not prove trade capacity or live deposits/withdrawals.
- `arbitrage_history.py` merges the latest published JSON's bounded history with a new scan. Observations are sparse (nominally hourly), may be lost when a deployment fails or previous URL cannot be retrieved, and do not establish continuous opportunity lifetimes. Current candidates are a truncated top-25 list; missing pairs are not necessarily closed.
- `arbitrage.html` links to the detail page. The workflow copies it to Pages. Unit tests cover snapshot merge. No execution permissions or wallet secrets are involved.
- **Pending validation:** green CI/Pages deployment, latest `arbitrage.json` containing `history`, navigation, and browser-level calculator functionality. This does not implement live multi-frequency sampling, verified minimum/maximum executable capital, or real withdrawal/deposit confirmation.

## سیاست توسعه بدون حذف قابلیت‌های موجود — 2026-10-30

**خط مبنای قابل بازگشت:** [backup/pendarcrypto-baseline-2026-10-30](https://github.com/nimania/crypto/tree/backup/pendarcrypto-baseline-2026-10-30)؛ این شاخه قبل از توسعه فازهای بعدی از `main` ایجاد شده است.

- تغییرات آینده **افزایشی** باشند و هیچ‌کدام از مسیرهای موجود (`index.html`، `coin.html`، `arbitrage.html`، `arbitrage-detail.html`، `calculator.html`، `guide.html`) یا هدر مشترک را بی‌دلیل حذف/جایگزین نکنند.
- اسکن DEX چندشبکه‌ای، همبستگی و ساختار BTC، آربیتراژ صرافی‌های ایران، اعتبارسنجی دفتر سفارش، محاسبه‌گر، تاریخچه، پیوندهای صفحه رمزارز و راهنما باید حفظ شوند.
- طرح روشن، قلم وزیرمتن و هویت «پندارکریپتو» حفظ شوند؛ بازطراحی نباید عملکرد داده‌ای را قربانی ظاهر کند.
- پیش از ادغام و انتشار: آزمون‌های فعلی، صحت HTML/JS و پیوندها، سازگاری schema JSON، و تهیه نسخه قبلی بررسی شوند. برای داده تازه از فیلد اختیاری و سازگار با گذشته استفاده شود؛ مصرف‌کننده‌های فعلی نباید بشکنند.
- برای هر قابلیت بزرگ، ابتدا شاخه مجزا/PR و آزمایش؛ انتشار روی `main` فقط پس از تأیید. در صورت مشکل، بازگشت به commit شناخته‌شده بدون پاک‌کردن داده‌ها.
- اسکن یا استقرار ناموفق نباید به‌صورت فرصت صفر یا سود قطعی نمایش داده شود؛ این محصول read-only باقی می‌ماند مگر با تصمیم مستقل و صریح کاربر.
- وجود شاخه پشتیبان به‌تنهایی پشتیبان‌گیری از تاریخچه خارج از مخزن یا اثبات سلامت آخرین استقرار نیست. تاریخچه داده‌ها نیز باید به‌طور مستقل پایدار و پشتیبان‌گیری شود.
