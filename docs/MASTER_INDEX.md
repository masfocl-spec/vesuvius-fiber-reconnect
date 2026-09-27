# MASTER_INDEX — единая система знаний проекта «fiber-reconnect»

**Дата:** 2026-09-28 (обновлено после сверки с итогами всех экспериментов).
**Главный результат проекта на сегодня — НЕ «метод B1», а: (1) на реальных предсказаниях
оптимум — A1 (дистанция + Hungarian one-to-one + τ), B1-геометрия на реальном шуме вредит
полноте; (2) ценность B1b выжила только как фильтр предложений; (3) advantage тангенса —
режим-специфичен (подробно §II, §III.0, §III.4).**
**Назначение:** единственная точка входа, связывающая ВСЕ документы,
код, данные, аудиты, внешние репозитории и выводы проекта. Ничего не должно существовать
вне этой карты; всё новое дописывается сюда и в соответствующий разделительный документ.
Структура: §I карта артефактов → §II единая постановка задачи → §III состояние экспериментов →
§IV внешняя среда (кто/что уже сделано) → §V атрибуции (не воруем) → §VI репозитории и код →
§VII данные → §VIII открытые вопросы и план → §IX хронология сессий.

---

## I. Карта артефактов рабочего пространства

```
elder scrolls/
├── MASTER_INDEX.md                  ← ЭТОТ ФАЙЛ (единая система)
├── PLAN.md                          ← УТВЕРЖДЁННЫЙ МАРШРУТ: этапы 0–4, ворота, дедлайн 31.10.2026
│
├── ── ДОКУМЕНТЫ-АУДИТЫ (все прочтены полностью) ──
├── project_audit.md                 Аудит постановки: сайт, villa-код, issues/PR, FPicker, литература
│                                    (вердикт: B1 = KNOWN IDEA, NOT USED HERE, категория B; §12 — план)
├── site_audit.md                    Полный аудит scrollprize.org: призы, Open Problems, датасеты
├── villa_audit.md                   Код-аудит fiber-стека villa: fiber_trace_3d, mutex, bracket_links
├── data_plan.md                     План данных: регион 256³ Paris4, слой 20260915, eval_fibers 65/65
├── KAGGLE_GUIDE_FOR_USER_AND_AGENT.md  Инфраструктура Kaggle CLI (для будущих GPU-прогонов)
├── evidence_matrix.csv              Claim-by-claim доказательная база (к проектному аудиту)
│
├── ── AUDIT ДАННЫХ СООБЩЕСТВА (Discord; все прочтены сплошно) ──
├── discord_audit.md                 Дамп #1: general 07–27.09.2026 (500 сообщ.) + §8 ранний фрагмент
│                                    2024-07…2025-06 + §9 досверка ссылок
├── discord_archive_audit.md         Дамп #2: general 04.05–06.09.2026 (1655 сообщ., v2-атрибуции,
│                                    §5a HF-бакет: 136 волокон Paris4, 328 branches; §9 полный проход)
├── discord_unrolling_audit.md       Дамп #3: #unrolling-vc3d 24.05.2024–24.09.2026 (1844 сообщ.):
│                                    loopy-BP waldkauz, fiber fingerprint, хронология linking
│
├── ── НАШ КОД И ЭКСПЕРИМЕНТЫ (B1) ──
├── fiber-reconnect/
│   ├── report.md                    Синтетический бенчмарк (NML-куб s1, 83 breaks, 3 seeds)
│   ├── real_region_report.md        Реальный пилот (лёгкий 256³) + трудный регион + ИНВЕРСИЯ
│   ├── reproduce.md                 Команды воспроизведения синтетики
│   ├── run_experiment.py            Синтетический пайплайн (A0/A1/B1a-c/B2/B3)
│   ├── run_real_experiment.py       Реальный пайплайн (presence→скелет→GT-привязка→методы)
│   ├── hunt_hard_region.py          Зондирование 9 окон (holes100-критерий)
│   ├── auto_hard_region.py          Автовыбор трудного региона (итог: 19456/9216/44032)
│   ├── src/fiber_reconnect/
│   │   ├── experiment.py            ЯДРО: corruption, endpoints (tangent/curvature/filters),
│   │   │                            costs, Hungarian, τ-acceptance, Bezier-коннекторы, скоринг
│   │   ├── nml_io.py                NML-парсер, chain decomposition, resampling
│   │   ├── eval_gt.py, viz.py       Оценка GT, визуализация
│   ├── data/raw/                    labelsTr/*.tif + nml/*.nml (fiber-skeletons Dataset001)
│   ├── data/fibers_tools.py, fibers-dataset-generator.py   (копии официальных конвертеров)
│   ├── outputs/                     results*.csv, tau_sweep*.csv, breaks_per_case.csv, fig1-7
│   ├── outputs_real/                results_real.csv, tau_sweep_real.csv
│   ├── rich_windows.json            9 зондировочных окон (score, holes-фракция, координаты)
│   ├── check_data.py, test_synthetic.py, download_*.sh   сани-чеки данных, юнит-тесты, фетчеры
│   ├── metadata.min.json / metadata_pretty.json   локальная копия метаданных бакета (gzip-json)
│   └── _research/fibers.pdf         FPicker (ECCV 2026) — первоисточник-референс
│
├── ── ДАННЫЕ (скачано, готово к работе) ──
├── data/pred/    region_presence/nx/ny.npy (256³ L1→базовые 2.4µm вокс., слой 20260915);
│                 hard_19456_9216_44032/ (трудный регион 512³); inference.json (provenance)
├── data/probe/   9 зондировочных окон (выбор региона) + rich_windows.json
├── data/ct/      region_ct.npy (L3, контекст)
├── data/spiral/  eval_fibers/ (65/65 ✅), abs_winding, relative_windings, umbilicus
├── metadata_paris4.json             Метаданные бакета Paris4 (16.9 МБ)
│
├── ── ОФИЦИАЛЬНЫЙ РЕПОЗИТОРИЙ (клон, изучен) ──
└── villa/                           ScrollPrize/villa (монорепо: spiral-fitting, lasagna,
                                     vesuvius, volume-cartographer/VC3D, foundation, …)
                                     + villa/scrollprize.org/ — клон исходников САЙТА
                                     (docusaurus; для сверки формулировок Open Problems)
└── discord/                         три дампа + распарсенные JSON/логи + HF-выкачка
    ├── messages.json/.txt           (дамп 1, 500 сообщ.)
    ├── archive/                     (дамп 2: archive_messages_v2.json, hf_fibers/ 136 файлов,
    │                                 hf_fibers_list.json, analyze_hf_fibers.py, парсеры v1/v2)
    └── unrolling/                   (дамп 3: unrolling_messages.json, unrolling_readable.txt)
```

---

## II. Единая постановка задачи (что мы вообще делаем)

**Проект — НЕ «метод B1». Это количественное исследование reconnection-базовой линии:**
абляционная лестница методов (A0 greedy / A1 distance+Hungarian+τ / B1a hard-tangent /
B1b soft-tangent / B1c / B2 +curvature / B3 +crossing) на одинаковых событиях, в двух режимах —
синтетическая коррупция (NML-куб fiber-skeletons) и реальные предсказания (Paris4 presence,
лёгкий и трудный регионы) — с целью установить, **какой ингредиент когда работает**, и дать
первый измеренный baseline для открытой проблемы Vesuvius (линковка волокон сегодня 100% ручная).

**Текущий главный вердикт (по совокупности экспериментов, §III):**
- **Рабочий оптимум на реальных данных — A1 (дистанция + one-to-one + τ).** Полнота 14/14
  (трудный) и 8/8 (лёгкий), 0 ложных, насыщение с τ=1.0.
- **B1 (tangent-aware) как метод — НЕ оптимум и в дефолтном виде не подходит** для реального
  шума: soft-tangent недобирает полноту (11/14 в лучшем τ против 14 у A1), hard-констрейнт
  необратимо убивает половину истинных пар (7/14), B2/B3 монотонно хуже. Причина: реальные дыры
  короткие (нет дистракторной конкуренции — дистанция уже однозначна), а тангенсы на рваной
  маске 19.2µm шумят так, что выравнивание штрафует истинные пары (villa#1357 подтверждён
  количественно).
- **Выжившая ценность B1b — фильтр предложений** для ревью-workflow: в «болоте» реального
  региона (7255 концов) даёт −45% предложений при большем числе истинных, чем A0/A1.
- **Преимущество тангенса — режим-специфично:** оно реально (85.5→96.4%, 9→0 false), но только
  в синтетическом режиме «длинные чистые разрезы с конкуренцией»; этот режим в GT-покрытых
  областях реального предсказания не встречается. Открыто: возникает ли он в compressed-зонах
  (villa#191/1829), где дистрактор систематически параллелен — не проверено.
- Практическая рекомендация отчёта: **если автосклейку делать — стартовать с A1; геометрию
  добавлять только после перекарлибровки на реальном шуме (вероятно, learned-веса), не с
  ручными весами.**

**Почему это нужно Vesuvius:** официальный spiral-fit потребляет ЦЕЛОСТНЫЕ волокна и ручные
cross-fiber линки (`resolve_fiber_links`, `bracket_fiber_links`, fiber-losses в `fit_spiral`);
линковка сегодня **100% ручная** (djosey 07.08.2026). Разрывы режут θ-биннинг бракет-линкера —
автоматический реконнект = недостающий этаж. Официальная цель (Open Problem 2026 №1):
«a connected graph representation».

**Точная ниша (по итогам трёх аудитов):** НЕ «первая автоматическая связь фрагментов» —
waldkauz уже пробовал assignment-оптимизацию с loopy BP («kind of works»), строит «fiberlets»,
bruniss+djosey озвучили «fiber fingerprint». Защитимая формулировка вклада:
**(1) первый количественный post-hoc reconnection baseline на официальных papyrus-данных;
(2) ablation-развязка с отрицательным результатом для ручной геометрии (сам по себе ценный
результат — он отсекает «очевидное» решение); (3) режимный анализ «когда тангенс работает»;
(4) фильтрующая ценность для ревью-workflow.** Категория новизны по project_audit §11:
**B (KNOWN IDEA, NOT USED HERE)** с C-элементами (домен; связка soft-tangent+Hungarian+τ;
negative results). Формулировка «tangent — фича, которая решает» НЕ защищена — только как
режим-специфичная.

---

## III. Состояние экспериментов: ВСЕ итоги всех прогонов (факты, чем проверено)

### III.0 Сводная таблица всех результатов (полнота/ложные, лучший τ)

| Режим | События | A0 greedy | A1 dist+Hun | B1a hard | B1b soft | B1c | B2 +curv | B3 +cross |
|---|---|---|---|---|---|---|---|---|
| Синтетика seed 20260926 | 83 | 57.8%/21 | 85.5%/9 | 91.6%/4 | **96.4%/0** | 96.4%/0 | 85.5%/0 | 83.1%/0 |
| Синтетика seed 7 | 83 | 67.9%/14 | 82.1%/9 | 88.1%/4 | **92.9%/0** | 92.9%/0 | 82.1%/0 | 79.8%/0 |
| Синтетика seed 42 | 83 | 53.5%/28 | 58.1%/31 | 90.7%/5 | 93.0%/2 | **94.2%/2** | 80.2%/0 | 80.2%/0 |
| Реальный лёгкий (gt) | 18 адр. | 8/0 | 8/0 | 8/0 | 7/0 (8 при τ2) | 7/0 (8) | 3/0 | 3/0 |
| Реальный трудный (gt) | 28 адр. | **14/0** | **14/0** | 7/0 (плато) | 6/0 (11 при τ2) | 6/0 | 3/0 | 2/0 |
| Реальный лёгкий (all) | 7255 концов | 5 true/3068 prop. | 3/3296 | — | **7/1830** | — | — | 2/621 |

**Читается однозначно: победитель зависит от режима. Синтетика → B1b; реальное → A1 (полнота)
и B1b (фильтрация). Ни в одном реальном прогоне ни один метод не дал ни одной ложной связи.**

### III.1 Синтетический бенчмарк (fiber-skeletons NML, куб s1_00497_01497_03997_256)

- 89 деревьев → 96 цепей; corruption: 83 разреза U[8,20] vox перпендикулярно; 163/166 концов видимы.
- **Канонический seed 20260926 (τ=1.2):** A0 57.8%/21 false → A1 85.5%/9 → B1a 91.6%/4 →
  **B1b 96.4%/0** → B1c 96.4%/0 → B2 85.5%/0 → B3 83.1%/0.
- Seeds 7/42 — тот же порядок (B1b 92.9%/0, 93.0%/2).
- τ-sweep: A1 сатурация 9 false — неустранимы дистанцией; B1b доминирует по всей границе;
  B1c≈B1b (hard-констрейнт избыточен при soft); B2 не выше B1b; B3 чуть хуже.
- Вывод: **soft tangent — причинный фактор** (85.5→96.4, 9→0 false); Hungarian сам по себе
  неразличим (A1≈A0 на seed 42); curvature/crossing не добавляют (negative result).
- Слабости: 1 куб/1 скролл, чистые перпендикулярные разрезы, GT-полилинии (не tracer-output),
  фиксированные веса, n мал для hard-subgroup.

### III.2 Реальный пилот (Paris4 256³, x16384 y9216 z44544, presence≥128, Lee-скелет)

- Same-space подтверждён (presence@GT 216/255 vs 16.7±4.6 контроль); GT-привязка r=4.0/cov≥0.5.
- Анатомия: дыры вдоль GT короткие (медиана 4 vox); доминирующая фрагментация — перекрёстки
  (68/98 концов отфильтрованы «маска продолжается» — корректно); адресуемых событий всего 18.
- Мир gt: **A0=A1=B1a 8/0; B1b/B1c 7/0; B2/B3 3/0** — все методы безошибочны, дистанции хватает.
- Мир all (7255 концов, мусор): **B1b 7 true при 1830 предложений vs A0 5/3068, A1 3/3296** —
  ценность B1 = фильтрация (−45% предложений, +true) для ревью-workflow.

### III.3 Трудный регион (512³, x19456 y9216 z44032; holes100=1.52 vs 0.99 пилот)

- 8 волокон → 104 фрагмента, до 29 кусков на волокно, 96 базовых разрывов, 28 адресуемых.
- Мир gt (τ=1.2): **A0=A1 14/0; B1a 7/0; B1b 6/0; B2 3/0; B3 2/0.**
- τ-sweep: A1 14/0 с τ=1.0; B1a плато 7 (hard-запрет необратимо убивает половину истинных);
  B1b →11 при τ=2.0 но не 14; B2→6, B3→3.
- **ГЛАВНЫЙ РЕЗУЛЬТАТ: на реальных предсказаниях иерархия инвертировалась — чистая дистанция
  (A1) доминирует, каждый геометрический член строго снижает полноту, ни один не даёт точности
  (false=0 у всех).** Механизм: короткие дыры (нет конкуренции в окне) + шумные тангенсы на
  рваной маске 19.2µm (villa#1357 подтверждён количественно). Практический вывод: стартовать
  с distance+one-to-one; геометрию — только после перекарлибровки (и, вероятно, learned-веса).
- Ограничения: 28 событий, GT-хрупкость (6→52 при вариации привязки), детектор видел
  eval-волокна, compressed-зоны (villa#191) не попали.

### III.4 Итоговая формула результатов (главный вывод проекта на сегодня)

**Синтетика (длинные чистые разрезы с дистракторами): tangent решает всё. Реальные
предсказания (короткие рваные дыры, шумные тангенсы): дистанция+one-to-one уже достаточна и
робастна; ручная геометрия вредит полноте.** Следствия для стратегии:

1. **Публиковать «B1 как метод» нельзя** — реальный оппонент скажет ровно то, что показали
   наши же трудные регионы. Публикабельная рамка: *baseline-study* (A1 как рекомендованный
   дефолт + B1b-фильтр + отрицательные результаты B1a/B2/B3 + режимный анализ).
2. **Открытый научный вопрос, который держит интерес:** не проверен режим, где тангенс
   обязан работать — compressed-зоны с систематически параллельным дистрактором соседнего
   витка (villa#1829/191). Если и там A1 безошибочен — история «геометрия не нужна» становится
   сильным самостоятельным результатом; если ошибочен — у B1 появляется честная ниша.
3. **Классическая ловушка закрыта τ-sweep'ом:** вывод «дистанции достаточно» не является
   пороговым артефактом (A1 насыщается при τ=1.0; B-варианты не догоняют ни при каком τ).

---

## IV. Внешняя среда: что уже сделано другими (сводка трёх аудитов Discord + сайта)

### IV.1 Команда (по данным #unrolling-vc3d 2024–2026 + general)

| Направление | Кто | Статус на 28.09.2026 | Отношение к B1 |
|---|---|---|---|
| Fiber-модели (presence+direction 7-канал, beam-трейс) | waldkauz | sd1 4.8µm + sd2 9.6µm на HF; инференс только 2.4µm-сканы | наш апстрим |
| Assignment-оптимизация кусков (loopy BP) | waldkauz | **приватно, НЕ опубликовано** (grep по villa: 0); «kind of works, needs less errors» | постановка-конкурент |
| «Fiberlets» (дискретная оптимизация коротких трасс) | waldkauz | анонс 16.08, кода нет в villa | мониторить |
| Ручной fiber linking (Kendra+LauraT, djosey) | команда | 113-волоконная сеть Paris4; фичи link/adjacent; **100% вручную** | наш GT и потребитель |
| Adjacent-winding линки (Δw=±1, `adjacent_branches`) | djosey (18.09) | формат определён; **spiral их ИГНОРИРУЕТ** (spiral_helpers:264 — «only supports same-winding») | незанятая ниша потребления |
| Fiber fingerprint (re-ID по окрестности через разрывы) | bruniss+djosey (21.09) | идея в чате, без кода | альтернативный механизм — атрибутировать |
| bracket_fiber_links (авто H-V kollesis-линки) | bruniss | в villa; требует ЦЕЛОСТНЫЕ волокна >1 витка | бенефициар нашего реконнекта |
| graph_patches (100k verified_patches из треков) | bruniss (30.07) | spiral_datasets/PHercParis4/verified_patches/ | данные |
| patch+fiber линкование | bruniss (сент.) | WIP; «test bed for patch linking»; fiber-patch-continuity (iluss) нашёл 179/347 размещений «листом мимо», фильтрация ухудшила fit | смежный фронт |
| Semi-auto annotation (Trace2CP) | waldkauz | в VC3D; сшивка fwd/rev — только дистанция | подтверждение нашей A-базовой |

### IV.2 Сообщество (кто близко подошёл)

- **thehja:** automatic fiber linking + graph traversal (~2025, брошено; вернулся 09.2026 —
  строит спираль 0332 из fiber-сплайнов; «fold cuts the whole sheet in fiber preds»).
- **qualzz:** fiber-spline авто-трейсер (3.3 см сплайн без человека); независимо упёрся в
  «link 2 parallel fibers»; геймификация разметки.
- **pscamillo:** constraint-gauge (sealed-бенчмарк winding-генераторов; E1 M1=0.923);
  winding-ruler; находка lasagna-hole-бага (#1183).
- **rodriguescarson:** labelscope (seam-детект перехода на соседний виток; z 0.4→11.5).
- **ShribyrLabs:** m7 orientation bias (03) + sheet-merge cutting (04) — пост-хок QA мешей.
- **joseph_11950:** winding-sync (L1-синхронизация; честный README), nml-toolkit.
- TAUIL-Abd-Elilah (iluss): fiber-patch-continuity (24.09) — ближайший смежный.
- Отрицательный результат (поиск по организации): Hungarian/reconnect/stitch для волокон —
  нигде; hackathon-проектов нет; в awesome-scroll-tools нет.

### IV.3 Ключевые даты среды (для контекста публикаций)

2026-06-25/27: статья arXiv:2606.29085 (PHerc1667 прочитан), $1M GP-2027; 2026-07: волна
открытости данных; 2026-08-05: djosey «linking is 100% manual»; 2026-09-18: adjacent-links;
2026-09-21: fiber fingerprint + waldkauz про loopy BP; 2026-09-24: fiber-patch-continuity.
**Окно для «первого автоматического линка» сужается — скорость публикации важнее полноты.**

---

## V. Атрибуции (мы не воруем — полный реестр)

| Идея/факт | Автор | Дата, место | Что обязаны сделать |
|---|---|---|---|
| Задача «bridging gaps between fibers» официально открыта | Vesuvius site | Open Problems 2026 | цитировать страницу |
| «Predictive model for missing/erroneous fiber connections» | Stephen (alumni) | 31.07.2024, Discord | первая публичная формулировка — цитировать |
| Vertex matching между штрихами для выбора продолжения | Kyle (об_article Hari) | 03.10.2024, Discord | прецедент матчинга — цитировать |
| Cost «endpoint distance + tangent + threshold» | Guo 2025 (коронары), Yang 2011/12, Bates 2018 | литература | related work, прямые прецеденты |
| LAP gap-closing | Jaqaman 2008; Kreshuk 2015 | литература | related work |
| FPicker (общая идея geometry-aware filament tracing; endpoint regression) | Zhao ECCV 2026 | arXiv:2609.08305 | «перенесли только общую идею»; FP НЕ делает reconnection (проверено) |
| Automatic fiber linking (CPU, graph traversal) | thehja | ~2025 / 07-08.08.2026 | явная атрибуция в related work |
| Assignment-оптимизация fiber pieces (loopy BP) | waldkauz | 21.09.2026 (#unrolling) | разделение формулировок в тексте о новизне |
| «Fiberlets» | waldkauz | 16.08.2026 | мониторить, упомянуть |
| Fiber fingerprint (re-ID по окрестности) | bruniss, djosey | 21.09.2026 | related work (альтернатива) |
| «Map same winding across breaks via fibers» | djosey | 28.07.2026 | цитата в мотивацию |
| «Only along fibers re-identify at large distance» | waldkauz | 08.07.2026 | цитата в мотивацию |
| Кроссинг-граф H/V как same-winding каркас | jrudolph (описание), команда (реализация VC3D) | 28.01.2025 / 2026 | учитывать при использовании branches |
| Synthetic scroll/surface zarrs с контролируемыми дефектами | willstevens, maxim_xyz, bruniss | 20.07.2026 | сослаться при описании corruption-методологии |
| Intersection-area как карта топологии | tomweidig | 09.10.2024 | историческая атрибуция |
| «if i can do it a model/optimizer can do it presumably» | bruniss | 04.09.2026 | цитата в мотивацию |
| constraint-gauge / sealed-protocol методология | pscamillo | 07-09.2026 | заимствовать протокол оценки |
| seam-признак кросс-виткового перехода | rodriguescarson (labelscope) | 30-31.08.2026 | кандидат reject-правила |
| Геометрический контроль утечки сплитов | pxnet (spiralcheck) | 03.08.2026 | применить к нашим сплитам |
| «Флаги ≠ фильтр» (проверять downstream-эффект) | iluss (fiber-patch-continuity) | 24.09.2026 | применить к нашим предложениям |

---

## VI. Репозитории и код (что просмотрено, что где лежит)

### VI.1 Официальный villa (локальный клон, изучен файлово)

| Файл | Что | Значение для B1 |
|---|---|---|
| `spiral-fitting/spiral_helpers.py` | `resolve_fiber_links` (потребитель ручных линков), `build_link_components`, `classify_fiber_hv`, **`load_fiber_point_collection` — adjacent_branches ИГНОРИРУЮТСЯ** (стр. 264, «no winding-offset representation») | место интеграции; незанятая ниша Δw-линков |
| `spiral-fitting/bracket_fiber_links.py` | `find_bracket_links`: θ-биннинг пересечений H×V, min_gap≤r_out−r_in≤max_gap, behind/in_front margins | требует целые волокна — бенефициар реконнекта |
| `spiral-fitting/fit_spiral.py` | интеграция волокон: direction loss, H/V радиальные смещения; ablation-конфиги no_fibers/no_fiber_links | куда вставлять результат |
| `vesuvius/.../fiber_trace_3d/trace2cp_tool.py` | beam-трейсер (width 8); **`fuse_forward_reverse_traces` — сшивка только по дистанции (2·gap+длины)** | официальная «анти-тангенс» точка сравнения |
| `vesuvius/.../fiber_trace_3d/{model,train,infer}.py` | 7-канальная модель (6 dir + presence), косинус-лосс; produced 20260915 | наш апстрим |
| `vesuvius/.../mutex_affinity_*` | Mutex Watershed аффинитеты (к волокнам НЕ подключены) | готовая инфраструктура learned-альтернативы |
| `foundation/datasets/fibers-dataset/*` | NML↔воксели, kimimaro, PCA H/V, detect-missed | переиспользовано в нашем коде |
| `volume-cartographer/apps/VC3D/LineAnnotationController.cpp` | ручные link/merge/split; `endpointTangentFromLinePoints` — тангенсы считаются, хранятся, НЕ используются для выбора | главный «отсутствующий» потребитель |
| `spiral-fitting/autoresearch.md` | протокол LLM-автоисследований спирали (метрика: total_fg_pixels ink) | контекст; их культура экспериментов |

### VI.2 Внешние репозитории (просмотрены через web)

- **TAUIL-Abd-Elilah/fiber-patch-continuity** — replay fit_spiral-линкера; 179/347
  fiber-patch пар «листом мимо»; фильтр ухудшил fit (0.363<0.414). Ближайший смежный.
- **pscamillo/constraint-gauge** — sealed pre-registered бенчмарк; local-tau; M1=1.000.
- **rodriguescarson/labelscope** — seam z-score; отказ-как-данные; 253 поверхностей.
- **abundantjoe/winding-sync** (+villa fork PR) — L1-синхронизация; бенчмарк 0.050 vs 0.670 self.
- **ShribyrLabs/vesuvius-reports** 03 (m7 orientation bias: Dice 0.29→0.52, merges 0.60→0.97)
  и 04 (ridge-cut: 1.62→0.38 pairs; no-op для released m7).
- **WillStevens/scrollreading** (simpaper: align_patches5, bigpatch; pipeline9-annealer;
  iluss replay) — классический стек автора «Patch connectivity».
- **joe-carr-data/windcheck** — самопересечения трасс; 5/84316 verified_patches; twist 9.4×.
- **Nicodol/spiralcheck** — утечки 54.8% в name-level сплитах.
- **aviad12g/tifxyz-doctor** — sentinel-пакеты; loc_valid PR#1264.
- **schillij95/graph_problem** — исторический (2024) sheet-stitching playground.
- Каталог без детального просмотра: scroll-truth, vesuvius-topo, 3ddct, vc-delta3d,
  sam2-cubes, autoseg_preprocess, khartes, MicroscopyNodes, winding-ruler, herculaneum-umbilici,
  umbilicus-cross-validation, scroll-anchor, scroll-cockpit, first-light-pherc0826, volcomp.
- **Попытки waldkauz (loopy BP assignment, fiberlets): код НЕ опубликован** — в villa grep
  belief_propagation/loopy/fiberlet = 0 попаданий. Проверен также его личный GitHub
  (hendrikschilling, 15 репо): единственный fiber-смежный — **FASP** (документация сабмита
  Automated Segmentation Prize 2024: surface pipeline на ceres, «fiber annotations» лишь в
  future work; BP — нет; assignment — только winding diffusion `vc_tifxyz_winding`).
  vesuvius_compressed_dl — сжатие прокси-данных. Публичные следы его fiber-работ =
  fiber_trace_3d/lasagna-fiber в villa + реплики в Discord. Мониторить его fork'и villa
  (branches) на появление fiberlets/BP.

---

## VII. Данные (инвентарь + проверенные факты)

| Набор | Где | Объём/состояние | Проверено |
|---|---|---|---|
| fiber prediction Paris4 слой 20260915 (presence/nx/ny) | S3 + data/pred/ | 256³ регион + hard 512³; **последний публичный слой** (S3: ровно 2 — 20260801 и 20260915) | листинг S3, presence@GT |
| eval_fibers Paris4 | ash2txt + data/spiral/ | **65/65 скачано = полный текущий набор** (~50 м волокон; «650-700» bruniss — про суммарные метры, файлов 65) | листинг 28.09 |
| HF `spiral/*/fibers` (ручные сети) | HF buckets | **4 свитка: Paris4 136, 0139 225, 0332 77, 1451 19**; Paris4 выкачан целиком (hf_fibers/, 67.5MB, 328 branches: 97% H↔V кроссинги, медиана угла 82.5°, 4 same-orientation пары, из них 2–3 ре-коннект-подобных) | API-листинг + полная выкачка |
| adjacent-линки `adjacent_branches` | формат в VC3D | **в Paris4-выгрузке 0/328** (поле появится после 18.09-анонса); spiral их игнорирует | grep выкачки + spiral_helpers |
| lasagna-fiber sd1/sd2 | HF scrollprize/lasagna-fiber | 4.8/9.6µm fiber-модели waldkauz (21.09) | анонс в чате |
| fiber-skeletons NML (Dataset001) | dl.ash2txt + fiber-reconnect/data/raw | 11 кубов; использован 1 (s1_00497...) | сани-чек 100% узлов на маске |
| spiral_datasets 26 свитков | ash2txt | Paris4: tracks/crossings.npz (2.9GiB), verified_patches (89-100k), winding_inference, fiber_directions.npz (2.74GB, 23.09), lasagna_inputs | листинги |
| ink labels | S3 segments/*/ink-labels | 28 сегментов (не наша задача) | jrudolph 22.09 |
| Ветка Christchurch ссылок | (из дампа 2) | fiber preds только для 2.4µm сканов | spelufo/waldkauz 01.09 |

**Про воронье/утечки:** eval-волокна могли видеть детектор при обучении (наш же отчёт,
ограничения); spiralcheck показал 54.8% утечек в name-level сплитах — наши GT-сплиты делать
геометрически.

---

## VIII. Открытые вопросы и план (сводный, по убыванию ценности)

**Стратегическая рамка (после инверсии на реальных данных):** проект стоит на развилке —
(а) рамка baseline-study уже достаточна для публикации (A1-дефолт + фильтр + negative results);
(б) спасти «геометрию» можно только перекарлибровкой (learned-веса, робастная оценка тангенса,
большее окно сглаживания) или переходом к fingerprint/окрестностным признакам (bruniss/djosey);
(в) практический разворот — suggestion-слой для ручного workflow, где фильтрующая ценность
B1b уже доказана деньгами (меньше кликов ревьюёров). Пункты ниже упорядочены внутри этой рамки.

1. **Compressed-зоны (villa#191-профиль)** — решающий эксперимент для судьбы «геометрии»:
   единственный непроверенный режим, где дистанция обязана ошибаться (систематический
   параллельный дистрактор соседнего витка, villa#1829). Критерий выбора региона: доля GT-точек
   с presence<64. Статус: критерий написан (auto_hard_region.py), но выбранный «трудный» регион
   всё ещё GT-богатый, не compressed — нужен выбор по точности модели, не по дырности.
2. **Adversarial corruption** (шум тангенсов по villa#1357-профилю, длинные гэпы 40–120,
   параллельный дистрактор, slanted-разрезы) — дешёвая фальсификация вывода «дистанции
   достаточно» до того, как заявлять его публично.
3. **Integration probe**: suggestion-слой top-k на dangling endpoints поверх ручного workflow
   (pending/approved) — метрика «сэкономленные клики»; GT = 330/666 волокон с ручными линками.
   Единственный тест на настоящих (не синтетических) концах в промышленном масштабе.
4. **Перекарлибровка тангенса** (если п.1 даст нишу): learned-веса (mutex-affinity стек villa),
   робастная оценка тангенса (усреднение по длинному хвосту, outlier-устойчивость), сравнение
   с fingerprint-признаками.
5. **Кросс-скролл**: сети 0139/0332/1451 на HF (без нового инференса для 0139 — есть 4.8µm preds).
6. **Δw=±1 adjacent-линки**: официальный резолвер их не потребляет — потенциальный
   «first consumer» в связке с нашим матчингом.
7. Статистика: McNemar/bootstrap на breaks_per_case.csv; weight-sweep для B2/B3.
8. Мониторинг: ветки waldkauz (fiberlets/BP), bruniss patch+fiber, djosey adjacent-consumer,
   пополнение eval_fibers и HF-сетей (растут еженедельно).

### VIII-a. Сводный план после сверки с site_audit (28.09, слияние с призовой механикой)

Уточнение приоритетов: пункты 1–3 выше остаются ядром, но упаковываются в маршрут с призовыми
воротами (механика из site_audit.md §2.4: ежемесячные Progress Prizes, гарантированные $20k
Best of the Month, дедлайны в конце месяца; судят early releases / принятие сообществом /
улучшения на реальных данных / документацию / адресацию Open Problems; форматы OME-Zarr +
VC3D fiber JSON; лицензия CC-BY-NC 4.0; без регистрации в Discord призы недоступны):

- **Этап 0 (сейчас):** регистрация Discord; публичный репозиторий baseline-study с полным
  реестром атрибуций §V с первого дня. Обоснование: IV.3 «окно сужается» — публичная отметка
  времени важнее полноты; публикация ≠ подача на приз.
- **Этап 1 (3–5 дн.):** п.2 (adversarial corruption — фальсификация «дистанции достаточно»)
  + **ценз фрагментации** (дыры vs перекрёстки vs неадресуемое, лёгкий/трудный/compressed)
  как отдельный деливерабл write-up'а; GT-сплиты только геометрические (урок spiralcheck,
  54.8% утечек в name-level); отбор compressed-региона по доле GT-точек presence<64 (не holes100).
- **Этап 2 (~неделя):** п.1 compressed-зоны — решающий ворота для судьбы геометрии.
- **Этап 3 (~неделя):** п.3 integration probe (GT = 330/666 волокон с ручными линками,
  метрика saved clicks) + **киллер-демо: bracket_fiber_links до/после реконнекта** (прирост
  same-sheet линков) → упаковка (VC3D fiber JSON pending, OME-Zarr) → подача в ближайший
  месячный цикл Progress Prizes.
- **Этап 4 (после):** кросс-скролл 0139 (готовые 4.8µm preds + 225 волокон сети), п.6
  (Δw=±1 adjacent — «первый потребитель»), McNemar/bootstrap, мониторинг веток waldkauz
  (периодичность: еженедельно, grep fiberlet/BP/assign в его fork'ах villa).

Две поправки к ранним формулировкам (сверка 28.09): (а) «grep по villa: 0 попаданий BP» —
верно для текущего кода, но belief_propagation существует в deprecated/thaumato-anakalyptor
(BP-2024 для ЛИСТОВ, предок линии waldkauz) — в related work упомянуть; (б) eval_fibers =
65 файлов = полный текущий набор (заметка site_audit про «66-й файл» — пересчёт листинга,
принято 65).

---

## IX. Хронология сессий (кто/когда добавил что)

- **2026-09-26:** замысел B1; data_plan (регион выбран по GT); скачано presence/nx/ny,
  eval_fibers 65/65, spiral JSON'ы; синтетический эксперимент (report.md).
- **2026-09-27 утро:** project_audit (код+сайт+литература, категория B); site_audit; villa_audit;
  data downloaded (hard region).
- **2026-09-27 день:** реальный пилот + трудный регион (real_region_report.md, ИНВЕРСИЯ).
- **2026-09-27 вечер:** Discord-дамп 1 (general 07-27.09; 500 сообщ.); досверка ссылок.
- **2026-09-27 ночь:** Discord-дамп 2 (archive 04.05-06.09; 1655 сообщ.; v2-репарсер атрибуций —
  492 исправления; полная выкачка HF-бакета Paris4: 136 волокон, 328 branches, кроссинговый
  граф — НЕ reconnection-GT); ранний фрагмент 2024-25 от пользователя (Kyle/vertex matching,
  jrudolph кроссинг-граф, sean skeleton-recall).
- **2026-09-28:** Discord-дамп 3 (#unrolling-vc3d 2024-2026; 1844 сообщ.): loopy-BP waldkauz,
  fiber fingerprint, хронология ручного линкования, 4-скроллные сети на HF, adjacent-линки;
  проверка fiber-patch-continuity; настоящий MASTER_INDEX (сведение всего).

---

## Правила ведения (из AGENTS.md, применённые здесь)

- Событийные метрики = сигнал тревоги пайплайна → проверять данные (сделано: same-space,
  presence@GT, листинги, md5 дубликатов дампов).
- Изменения метода ≠ багфиксы; GT/оценка не менялись вместе с методом.
- Всё проверяемо: id сообщений, коммиты, URL, листинги в аудтах; данные воспроизводимы
  (reproduce.md; inference.json provenance).
- Не оптимизировать метрику порогами без обоснования (τ-sweep вместо подгонки).
