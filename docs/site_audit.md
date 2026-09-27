# Полный аудит сайта Vesuvius Challenge (все разделы)

**Дата:** 2026-09-27. **Метод:** 4 параллельных агентских прохода (призы/проблемы/вехи; данные; туториалы; сообщество/блог/архив) по живым страницам vesuviuschallenge.org = scrollprize.org, с перекрёстной проверкой по артефактам S3-бакета и dl.ash2txt.org. Все факты с URL; недоступное помечено.
**Сводка сайта:** открыто призов на $2,140,000; выдано $1,868,000 с 2023; отсканировано 45 свитков/фрагментов; 1 свиток прочитан целиком; чернила видны на 9 из 45 сканов.

---

## 1. Карта сайта (фактические URL)

**Навигация:** `/` (главная) · `/prizes` (единственная страница призов) · `/2026_open_problems` (Problems) · Tutorials & in-depth: `/tutorial_VC3D`, `/tutorial_spiral`, `/open_problems/winding_annotations`, `/tutorial5` · `/data_browser` (Data) · `/winners` (Milepoints — отдельной страницы /milestones НЕТ, нав ведёт на /winners) · Community = внешние ссылки (Discord, X, Substack, GitHub, HuggingFace, W&B) · `/press` · Donate (Stripe) · `/get_started`.

**Сайдбар:** `/data` (форматы) · `/data_datasets` (курируемые датасеты) · `/faq` · `/villa_model` (Extra) · `/master_plan` (Archive) · `/jobs` · `/community_projects`.

**404 / особенности:** `/open_prizes`, `/milestones`, `/results`, `/2026_prizes`, `/prizes_2027`, `/2027_prizes`, `/2027_grand_prize`, `/2023_prizes`, `/community`, `/tutorials`, `/khartes` — 404. `/tutorial4` — 200, но пустая страница. `/community` — нет, это дропдаун внешних ссылок. Отдельной страницы Grand Prize 2027 нет — канонический источник `/prizes#2027-grand-prize`.

---

## 2. Призы (https://scrollprize.org/prizes; все открыты до 25 июня 2027)

### 2.1 2027 Grand Prize — $1,000,000 ($800k/1-е, $100k/2-е, $50k/3-е, $50k/4-е)
- Задача: полностью развернуть и сделать читаемым один из **13 допустимых сканов** (список = в точности список пользователя, с ID сканов): PHerc0125 (20250821151825), PHerc0191 (20250821151635), PHerc0211 (20250821151803), PHerc0257 (20250821151750), PHerc0268 (20251110183117), PHerc0358 (20250821151737), PHerc0800 (20250521135224), PHerc0813 (20250821151723), PHerc0826 (20250821151701), PHerc1203 (20250820131727), PHerc1218 (20250521120456), PHerc1447 (20250521151220), PHerc1545 (20250821151648).
- Требования: 100% recto-поверхности (до 10% отклеенных кусков можно пропустить), ≥70% символов каждой колонки читаемо посимвольно; open-source, интеграция с VC3D, Docker-воспроизводимость, **≤8 часов ручного труда**, тренировочные данные под CC-BY-NC 4.0, фиксированные сиды, публичный эксперимент-трекинг, нет пересечения train/predict, false-positive mitigation + held-out валидация. **Нельзя использовать данные, полученные со сканов выбранного свитка в большем разрешении.** Обязательна регистрация в Discord.
- Судьи: Technical Team воспроизводит, независимая Papyrology Team оценивает читаемость; первый прошедший требования выигрывает.

### 2.2 First Letters Prizes — $500,000 ($50k × до 10 свитков)
- 10 букв на площади 4 см²; tifxyz-меш, масштабные линейки, методология, false-positive mitigation, held-out, open-source после победы.
- Элайджибл — **другой список из 22 томов**: 13 выше МИНУС PHerc1447, плюс PHerc0175A/B, 0306B, 0343, 0483A/B, 0490A/B, 0846A/B (полный список на /prizes).

### 2.3 PHerc. Paris 4's Title Prize — $50,000 («Submissions remain open until the prize is won»)
- Титул Scroll 1 (любой том, включая 2.4µm); «сами читать титул не обязаны»; титулы PHerc.172 и PHerc.139 уже сняты; зона титула Paris 4 «пока не показывает детектируемого чернильного сигнала».
- **Разрешение старого противоречия:** в мае 2025 вручили $60,000 First Title Prize за титул **PHerc.172** («Philodemus, On Vices, Book 1(?)», Roth & Nowak) — это ДРУГОЙ приз; текущие $50k — за Paris 4. Homepage-строка «$50,000 PHerc. Paris 4's Title» корректна.

### 2.4 Progress Prizes — $590,000/год; ежемесячно, следующий дедлайн **30 сентября 2026**
- Гарантированные «$20,000 Best Submission of the Month»; тиры $20k/$10k/$5k/$2.5k/$1k/$500/$250. Судят: ранние релизы, принятие сообществом, улучшения на реальных данных, документация; работа должна адресовать Open Problems или VC3D; стандартные форматы (OME-Zarr, tifxyz).
- **Недавние награды, показательные для нас:** июль 2026 — $2,500 «Patch connectivity» (William Stevens, «annealing-based optimisation to find consistently-connected regions from noisy patches»); август 2026 — $20,000 «Patch-based unwrapping on PHerc. 1667 (~365 см²)» (он же); май 2026 — $10,000 ScrollFiesta (auto-mesher, Ben Kyles); июнь 2026 — $1,000 «Fiber format converter» (Joseph Balmaceda, NML→CSV/JSON/SWC).

### 2.5 Архив 2024 (закрыт 31.12.2024; /2024_prizes)
- 2024 Grand Prize $200k («Read 90% of 4 scrolls from Scrolls 1–5») — не присуждён полностью; **First Automated Segmentation $100k (первоначально)**: «автосегментация региона GP-2023 в Scroll 1, ≤4 ч ручного труда, ≤48 ч вычислений» — вручено дек 2024 по $30k Schilliger&Johnson и Henderson; First Title/First Letters 4×$60k; Progress ~$350k/год (вишлист тогда: сшивка листов ThaumatoAnakalyptor, сегментация сжатых регионов, 3D-чернила).

---

## 3. Открытые проблемы

### 3.1 /2026_open_problems (обновлена ~июль 2026)
- 1. Сканирование: сжатые регионы рассеивают пучок; непонятно, какой этап пайплайна виноват, когда чернил нет.
- 2. Unwrapping: «Ни один метод не трассирует полную корректную поверхность свитка автоматически»; **«качество меток — один из главных бутылочных горлышек развёртки»**; направления: snapping меток, active learning, «лучше метки, а не просто большие модели».
- 3. Чернила: псевдо-разметка не гарантирована на новых свитках.
- 4. Масштаб данных (инфраструктура).
- Области вклада: (1) recto-метки/топология (предложены distance-transform представления); (2) мешинг/починка топологии — дыры, слияния, перескоки листа (инструмент сообщества ScrollFiesta); (3) качество меток; (4) **Fiber tracing** — «robust fiber tracing is exactly this kind of problem» (для людей из classical CV / point tracking / коннектомики); принцип: «трассировщик, уверенно ведущий меньше волокон, полезнее»; упомянуты чекпойнты **fiber_hz_vt** (nnU-Net на ручных H/V 7.91µm), тренер `scripts/fiber_5class` (фон/V-волокно/H-волокно/чернила), `fiber_dinoguided_2class_step010000`; VC3D-трассировщик полуручной; (5) spiral fit/winding; (6) прямая 3D-сегментация чернил (продемонстрирована на Paris 4, `ink_3d_dino_guided`) + self-supervised DINO.

### 3.2 /open_problems/winding_annotations (обновлена 12.07.2026) — «наша» страница
- Winding constraints = «точки, линии, волокна или патчи поверхности, чьё отношение к виткам свитка известно». Три типа: same-winding («трассированное волокно даёт свидетельство вдоль одного витка»), relative, absolute.
- Стратегический разворот: «локальные точные констрейнты (а не полная сегментация витка) — самый быстрый путь к развёртке свитков в масштабе».
- Констрейнты могут быть «нарисованы вручную, **выведены из волокон или мешей**, получены классическим CV, предложены обученной моделью…» — автоматизация прямо запрошена.
- Непопробованные идеи (их же список): нарисованные пути — «могли бы дать **лучшую связность, чем разорванные волокна**» (ключевая цитата для нас); чернильные линии как same-winding; межколонные промежутки; **коллизеи** (склейки листов) — «выделяются в CT и подходят под deep learning».
- Инструменты: VC3D, spiral-fitting в villa, spiral-input датасет. Баунти на странице нет.

---

## 4. Туториалы и in-depth

### 4.1 /tutorial_VC3D — Virtual Unwrapping с VC3D
- Воркфлоу: открыть CT (пример — **PHerc1447** из вашего списка!), сегментация GrowPatch (ctrl+right click, ~35 итераций), редактирование ключами 1–5.
- Критерий качества сегмента — видимость волокон: «качественный сегмент следует листам, и горизонтальные/вертикальные волокна отчётливо видны в развёртке».
- Winding-аннотации в VC3D: патчи, point collections, волокна. Категории same/different winding.
- **Волокна (same-winding):** 4-панельный инструмент ручной расстановки control points с интерполяцией/экстраполяцией через lasagna-нормали. Трассировка ручная, точка-за-точкой, с пер-точной переоптимизацией.
- Point collections можно использовать «как рёбра в графе патчей, если хотите соединить разреженные патчи» — единственное явное «соединение» на странице.
- Ссылки: релизы villa (GitHub), Docker `ghcr.io/scrollprize/villa/volume-cartographer:stable`.

### 4.2 /tutorial_spiral — Spiral Fitting
- Мотивация: низходящие инструменты «останавливаются, упёршись в сложный регион»; склеивать патчи напрямую трудно, «особенно там, где между ними дыры».
- Модель: архимедова спираль + диффеоморфизм (не рвёт и не сминает лист); каждый вход — дифференцируемый лосс; совместная оптимизация Adam ~30k шагов; код `spiral-fitting/` в villa; статья arXiv:2512.04927.
- **Входы (все с тумблерами):** верифицированные патчи; same-sheet полосы/линии — «point collections, нарисованные в VC3D, ИЛИ волокна, протрассированные в VC3D»; relative/absolute winding; `drawn_control_points`; волюметрика — нормали, grad-mag, скелетные треки, **`fiber_directions.npz`**, умбиликус (обязателен), внешняя оболочка. Тумблеры: `input_use_fibers`, `input_use_fiber_directions` и др.
- Цитата о роли волокна: «патч в одном регионе, волокно в другом, пара relative-winding аннотаций в неоднозначном месте — подгонка объединяет это в одно глобально согласованное решение».
- **Что осталось ручным:** умбиликус — «автоматического метода нет, человек читает его с CT в VC3D». Волокна — «протрассированы в VC3D» (ручные control points).
- Ограничения: треки по умолчанию выключены; zarr-скейлы «легко тихо перепутать»; память GPU для целого свитка; модель чернильного покрытия обучена только на Paris 4; статья описывает более старый tracks-only сетап, текущий код опирается на курируемые evidences.
- Референсный датасет: spiral-input Paris4 (в туториале «~90 GB», на странице датасетов «~49.6 GB» — расхождение на сайте).

### 4.3 /tutorial5 — Ink Detection
- Финальный шаг: 3D-подобъёмы вдоль поверхности → 2D карта вероятности чернил, сшивка с Hann-окнами; обучение на IR-фото фрагментов + консервативные итеративные метки.
- SOTA: U-Net vesuvius_unet; кросс-скролловый гибрид «3D-stem + 2D U-Net», 29 представлений, 4 свитка; чекпойнты `scrollprize/ink_9um` на HF. Режимы flat 2.5D и native 3D (последний предпочтителен).
- Про волокна: ни слова — этап независим.
- Ссылка на статью прочитанного свитка: arXiv:2606.29085.

### 4.4 Архивные in-depth
- `/unwrapping` (обзор): два SOTA-подхода — spiral fitting (pmh47/spiral-fitting) и surface tracer (hendrikschilling/FASP); «в развёртке лист почти прямоуголен, с локально перпендикулярными волокнами»; spiral fitting «навязывает согласование V/H-волокон при развёртке»; главный фейл — «прыжок через виток».
- `/segmentation` (архив, фев 2025): VC3D-мешевой туториал; **упоминает готовые fiber-direction поля для Scroll 5 (PHerc172) на dl.ash2txt.org** (горизонтальное поле считано только с z2000:z8000, вертикальное — на всю высоту) — волоконные поля существуют и за пределами «старой пятёрки» S3.
- `/tutorial1..3`, `/tutorial_VC`, `/ink_detection` (старая призовая страница $100k). `/tutorial4` — пустая.

---

## 5. Данные

### 5.1 Data Browser — https://scrollprize.org/data_browser
- Индекс всех 45 образцов (35 свитков + 10 фрагментов) со статусами: «Full scroll read» (PHerc.1667), «Substantial text» (172), «Title found» (139), «Ink detected» (9 шт), «Segmenting», «Scanned».
- По новым 2025-сканам: почти все «Scanned», 0 сегментов; **исключения: PHerc800 — 6 сегментов, PHerc1447 — 15** (auto_grown); «в сегментации»: 490B, 483B, MAN5.
- Ссылки ведут в S3-бакет; сам браузер — JS-приложение (статически список не парсится).

### 5.2 Data Formats — /data
- Два набора: «Vesuvius Challenge — CT Scans of Herculaneum Papyri» (текущий) и «EduceLab-Scrolls» (легаси, Scrolls 1–4 + фрагменты до 2025).
- Хостинг: `s3://vesuvius-challenge-open-data/` (AWS Open Data, бесплатно ≥2 года), индекс https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/index.html.
- Форматы: объёмы OME-Zarr (основной) / TIFF; поверхностные объёмы OME-Zarr/TIFF; меши OBJ + TIFXYZ; выходы моделей OME-Zarr/TIFF; метаданные JSON. Раскладка `{SAMPLE}/volumes|segments|representations` (predictions внутри representations). Лицензия **CC-BY-NC 4.0** (легаси — © EduceLab/UKY).
- **Важно:** сама страница /data НЕ документирует lasagna-манифесты, presence/nx/ny, VC3D fiber JSON, умбиликус — это живёт в туториале spiral и в самих артефактах.
- Верифицированная структура fiber-предсказания (скачанный манифест Paris4 20260915): `.lasagna.json` v2 с группами `presence`/`nx`/`ny` (scaledown 3), `base_shape_zyx [75784, 32693, 32693]`, provenance в `inference.json` (`artifact_kind: "fiber3d-prediction"`, чанки 64³, blosc/zstd, uint8).
- VC3D fiber JSON (из eval_fibers): `branches`, `control_points[].segment_to_next` с полным конфигом трассировщика (`beam_width: 8`, `cone_angle_degrees: 25.0`, `step_voxels: 4.0`, `smoothness_tangent_weight: 10.0`…), `optimizer: native_fiber_trace3d`, `tracer_version: 2`.

### 5.3 Curated Datasets — /data_datasets
**Текущие (пайплайн июля 2026):**
| # | Датасет | Дата | Содержимое | Размер | Хост |
|---|---|---|---|---|---|
| 001 | spiral-input | 2026-07 | Paris4: ~27k верифицированных + ~204k невериф. патчей, треки, point collections, same/relative/abs_winding графы, умбиликус, **fiber + outer-shell геометрия**, входы подгонки | ~49.6 GB (~905k файлов); в туториале ~90 GB | dl.ash2txt.org/datasets/spiral_datasets/PHercParis4/ |
| 002 | surface-labels | 2026-07 | вокселизованные recto-поверхности + объёмы для ML | не указан (HF-бакет ~3.68 TB всего) | HF buckets scrollprize/datasets/surfaces |
| 003 | ink-labels | 2026-07 | бинарные чернильные маски 2D/3D, псевдо-разметка | ~804 GB / ~2.38M файлов | HF buckets …/ink (phercparis4, 0009b, 0139, 0500p2, 1667, 814, 841, man5) |

**Архивные (баннер OUTDATED):**
| # | Датасет | Дата | Содержимое | Хост |
|---|---|---|---|---|
| 004 | fiber-skeletons | 2025-07 | «мануально аннотированные волокна papyrus — пряди листа»; кубы 256³/512³, каждое волокно протрассировано в WEBKNOSSOS; nnU-Net формат; NML в Dataset001_sk-fibers-20250124/nml | dl.ash2txt.org/datasets/fiber-skeletons/ (zip 422 MB) |
| 005 | volumetric-instance-labels | 2024-10 | Scroll 1, кубы 256³, .nrrd volume+instance; «harmonized — recommended starting point» | dl.ash2txt.org |
| 006 | grand-prize-banner-region | 2024-12 | регион GP-2023: меши 288 MB, объём 77 GB zarr, tifstack 389.9 GB, medial-surface предсказания | dl.ash2txt.org |

**На сервере, но НЕ на странице:** `seg-derived-recto-surfaces` (2025-02-15): recto-метки для scrolls 1, 4 и немного 5; nnU-Net imagesTr/labelsTr.

### 5.4 dl.ash2txt.org — фактические листинги
- `datasets/`: fiber-skeletons, grand-prize-banner-region, seg-derived-recto-surfaces, spiral_datasets.
- **fiber-skeletons содержит 4 версии (в README не упомянуты):** Dataset001_sk-fibers-20250124, **Dataset002_sk-fibers-hzvt-20250228, Dataset003_sk-fibers-hzvt-20250404** (с H/V-метками!), Dataset004_sk-fibers-binary-20250728.
- `spiral_datasets/` — **26 свитков, включая ВСЕ новые 2025-сканы** (папки от 2026-07-30): у новых пока только `tracks/`; PHercParis4 — полный набор: `eval_fibers/` (**66 файлов**, а не 65 — на один больше, чем мы качали), `lasagna_inputs/`, `outer_shell/`, `verified_patches/`, `winding_inference/`, `abs/relative/same_windings.json`, `umbilicus.json`, **`fiber_directions.npz` (2.6 GiB, датирован 2026-09-23 — новее README)**.

### 5.5 S3-структура по новым свиткам (проверено листингом)
- У всех 13: `photos/`, `volumes/`, `representations/` (lasagna + surfaces predictions, у части — umbilicus). **fiber-predictions у 13 новых НЕТ.**
- `predictions/fibers/` существует у «старой пятёрки»: Paris4 (два прогона: 20260801084232 и 20260915212757), PHerc0139, 0332, 1299, 1451 (проверено листингом ранее).
- **PHerc1203 имеет второй том: rescan 2026-03-19, 2.403µm** + `segments/raw/`; PHerc1447 — ~15 auto_grown сегментов. (Правило GP: данными с более высокого разрешения выбранного свитка пользоваться нельзя.)

### 5.6 FAQ — /faq (36 вопросов)
- Разрешение: «7.91µm может хватать… свежие полные сканы 2.4µm, малые регионы до 1.1µm». Интенсивности: float32 ~[-0.1, 0.1], перцентильное окно. Новые объёмы — cloud-optimized OME-Zarr.
- Прямая 3D-сегментация чернил возможна без сегментации поверхности (Paris 4, `ink_3d_dino_guided`); цена — теравоксельные данные.
- Устройство papyrus: два перпендикулярных слоя волокон, лист ~100µm, текст на recto (горизонтальные волокна); чернила — «сироп, заполняющий ячейки вафли» между волокнами.
- Kaggle в дата-секции не упоминается вовсе; новые свитки — только Data Browser/S3.

---

## 6. Вехи и победители (таймлайн из /winners, /grandprize, /firstscroll, блога)

- **12.10.2023** — первые чернила (Handmer) + первое слово «ΠΟΡΦΥΡΑϹ» (Farritor, $40k).
- **31.12.2023** — Grand Prize $700k: Nader/Farritor/Schilliger (PHerc.Paris.4, ~5% свитка).
- **Дек 2024** — First Automated Segmentation: $30k Schilliger&Johnson + $30k Henderson.
- **05.05.2025** — First Title $60k: Roth & Nowak, PHerc.172 («On Vices, кн. 1(?)»).
- **Ноя 2025 – март 2026** — Kaggle Surface Detection $200k (победитель «Vesuvius Team» $60k; топ-10 в осн. ансамбли ResEncUNet/nnU-Net; модели переобучат на 2.4µm).
- **25.06.2026 (объявлено 15.07 в Неаполе)** — **первый свиток прочитан целиком: PHerc.1667**, ~22 колонки/~1.4 м, стоический трактат II в. до н.э. с именем Аристокреона (статья arXiv:2606.29085, код villa); титул PHerc.139 — Филодем «О богах», кн. 8; ~70% PHerc.172 развёрнуто; чернила Paris 4 показаны прямо в 3D.
- Всего выдано $1,868,000 (2023: ~$1.2M; 2024: ~$0.4M; 2025: ~$0.1M; 2026: ~$0.27M).
- Волокно-реле: $20k «Fiber following» (Johnson, сент 2024) → $1k «Fiber format converter» (Balmaceda, июнь 2026).

---

## 7. Сообщество, пресс, организация, архив

- **Community** — только внешние ссылки: Discord (https://discord.gg/V4fJhvtaQn; **обязателен для участия в призах**; из этой среды недоступен), X, Substack, GitHub, HuggingFace, W&B. Форума/календаря на сайте нет; office hours несколько раз в неделю (анонсы в Discord/блоге).
- **Press** — страница только для контактов прессы; списка освещения на сайте нет.
- **Организация:** Scroll Prize, Inc., 501(c)(3), «создана исключительно ради Геркуланумских папирусов»; основатель Nat Friedman (вклад $2.75M), со-спонсоры Musk Foundation ($2,084,000), Alex Gerko ($450k); внутренняя команда не участвует в призах, работает open-source; «exists to make the community faster, not to race it».
- **Archive /master_plan** (план от 25.07.2025): Stage 2 — $5–6M; Stage 3 — прочитать ~300 свитков ($4–8M); Stage 4 — ре-раскопки виллы; целевая стоимость развёртки $5,000/свиток (сегодня $1–5M).
- **Extra /villa_model** — LEGO-модель Виллы папирусов (забавно, нерелевантно).
- **Donate** — Stripe-чекаут (JS-only, содержимое нечитаемо).

---

## 8. Блог (https://scrollprize.substack.com; 67 постов, фев 2023 – авг 2026)

Полный индекс: 2026 — Aug 18 «From CT Scan to Ancient Text: A First Letters Prize Workflow»; Aug 6 «$33.5K awarded in July»; Jul 15 «A New $1M Grand Prize for 2027»; Jun 5 «The hard parts are getting clearer»; Mar 19 «We are cooking»; Jan 13 «~70% of PHerc. 172 is now digitally unwrapped». 2025 — Dec 21 «Finally—letters in Scroll 4!»; Nov 13 «Back to the Challenge: $100K Kaggle Surface Detection»; Oct 9 «Multiple scrolls now show Greek letters»; Sep 11 «Column of text from PHerc. 172»; Aug 15 «Unveiling the Mystery of Compressed Regions»; Jul 4; Jun 13; May 23; May 5 «$60,000 First Title Prize Awarded!»; May 1; Apr 25 «Scanning Herculaneum Scrolls at Scale»; Mar 12 «February Progress Prizes» (Dataset002 волоконный, 5-классная модель); Feb 27; Feb 5; Jan 24×2; Jan 23; Jan 21. 2024–2023 — 41 пост (полный список у агента; ключевые: Jun 4 2024 «New scroll CT data released», Nov 27 2024 «First letters found in new scroll», Feb 8 2024 GP-2023).

**Ключевые разборы:**
- **«The hard parts are getting clearer» (05.06.2026):** модели поверхностей у сегмента команды «около насыщения»; «плотные, скрученные и порванные регионы всё ещё ломают автоматику»; ручная аннотация не масштабируется; **полуавтоматическая трассировка волокон в Lasagna/VC3D — «2 см волокна в минуту»** там, где держится латент; пивот к self-supervised 3D DINO.
- **«February Progress Prizes» (12.03.2025):** выпущен Dataset002 — 7 волоконных кубов с метками H/V/пересечения (в т.ч. два 512³: сложенная спираль Scroll 5 и смятый/рваный регион Scroll 1a); 5-классная мульти-таск модель (recto/verso/H/V/intersections); @hja — ранняя работа «создания сегментаций из волокон».
- **«Unveiling the Mystery of Compressed Regions» (15.08.2025):** 0.55µm-скан PHerc.500P2 на ESRF ID11: «каждое волокно окружено толстой стенкой клеток, полость (люмен) внутри клеток отчётливо видна» — физическая природа «муты»; идеальный пиксель <1µm; лучшие рецепты 0.55µm/7cm/65keV и 2.4µm/22cm/77keV.
- **«A New $1M Grand Prize for 2027» (15.07.2026):** анонс в Неаполе; PHerc.1667 прочитан; Paris 4 пересканирован на 2.4µm на ESRF BM18 (~140 колонок).
- **«Scanning Herculaneum Scrolls at Scale» (25.04.2025):** 20 свитков за одну сессию на Diamond Light Source (с EduceLab/UKY, Biblioteca Nazrale, Univ. Naples Federico II); фотограмметрия, 3D-печатные ложементы, PTFE-плёнка, «double-double» сканы; цель — все ~300 свитков.
- **«From CT Scan to Ancient Text» (18.08.2026):** рекомендованный воркфлоу First Letters: spiral fitter основной, GrowPatch фолбэк; **качество сегментации оценивается по «непрерывным горизонтальным и вертикальным волокнам»**; финально — ink_9um.
- **«~70% of PHerc.172» (13.01.2026):** VC3D-пайплайн >10× быстрее полностью ручного VC; оставшийся ручной шаг — «sheet switches»; верхние 30% «слишком смяты»; 7.9µm «около практического потолка».

---

## 9. Что это значит для нашего проекта (кратко)

1. **Нашем направлению официально дана цена и очередь:** Winding Constraints прямо запрашивает автоматизацию same-winding констрейнтов «из волокон», а фраза «лучшая связность, чем у разорванных волокон» — дословная формулировка нашей задачи. Progress Prizes платят за связность ежемесячно (Stevens, июль–август 2026).
2. **GT-инфраструктура шире, чем мы использовали:** 4 версии fiber-skeletons (включая hzvt-версии с H/V-метками), 66-й eval_fiber, `fiber_directions.npz` 2.6GB (свежее README), fiber-поля PHerc172 (dl.ash2txt), чекпойнты fiber_hz_vt / fiber_5class / fiber_dinoguided.
3. **Дедлайн-рамка:** всё закрывается 25.06.2027; Progress Prizes — ежемесячно (след. 30.09.2026); для участия обязателен Discord (нужно зарегистрироваться заранее).
4. **Лицензия CC-BY-NC 4.0** на данные и требование GP выпускать тренировочные данные под той же лицензией — наш будущый артефакт должен это учитывать.

---

## 10. ЧТО БЫЛО УПУЩЕНО в прошлых проходах (дельта этого аудита)

1. Список 13 свитков = элайджибл-список Grand Prize 2027 с точными ID сканов; First Letters — ДРУГОЙ список из 22 томов (без PHerc1447).
2. Разрешение противоречия First Title ($60k за PHerc.172 ≠ открытые $50k за Paris 4).
3. fiber-skeletons существует в 4 версиях (наши синтетические кубы — из одной; hzvt-версии с H/V-метками мы не знали).
4. spiral_datasets раскатан на 26 свитков (все новые — с tracks/), у Paris4 есть `fiber_directions.npz` 2.6GB (2026-09-23) и 66-й eval_fiber.
5. Активное финансирование связности: Stevens $2.5k + $20k; ScrollFiesta $10k+$20k.
6. Чекпойнты fiber_hz_vt / fiber_5class / fiber_dinoguided упомянуты на открытых проблемах.
7. Скорость официальной волоконной аннотации: 2 см/мин (полуавтоматика); полные конфиги трассировщика внутри eval_fiber JSON (beam 8, конус 25°, шаг 4 voxel).
8. PHerc1203 пересканирован на 2.403µm (2026-03-19); PHerc800/1447 уже имеют сегменты; правило GP о запрете высокорез. данных.
9. Требования GP 2027 (8 часов ручного труда, CC-BY-NC, Docker, VC3D-интеграция) и Progress Prizes (стандартные форматы, адресация Open Problems).
10. Физика сжатых регионов (клеточные стенки/люмен, 0.55µm); критерий качества сегментации по непрерывности волокон (Aug 2026 workflow); коллизеи как кандидат для DL; мастер-план (300 свитков, $5k/свиток).
11. fiber-direction поля PHerc172 на dl.ash2txt.org (вне S3 «старой пятёрки»).
12. Полный таймлайн вех (включая PHerc.1667 целиком 25.06.2026, PHerc.139 титул, Paris4 3D-чернила) и полный индекс блога.

## 11. Что остаётся недоступным (принципиально)

- **Discord** (обязателен для призов) — не публичен из этой среды; регистрация нужна делать руками.
- Data Browser — JS-приложение (список получен агентом через рендер/кэш, структура подтверждена S3-листингами).
- Google Docs: «ESRF BM18 Draft Info Sheet (May 2025)» и EduceLab data sheet — за логином.
- vesuviuschallenge.substack.com — НЕ активная публикация (редирект; активен scrollprize.substack.com).
- Stripe-страница донатов — JS-only.
