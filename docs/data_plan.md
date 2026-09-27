# data_plan.md — минимальный real-data benchmark для B1 на PHercParis4

**Дата:** 2026-09-26. **Статус:** регион найден и верифицирован зондированием; часть данных скачана.
**Принцип:** реальный CT → официальное fiber prediction → реальные фрагменты → наш неизменный B1 → проверка
каждого proposed link относительно известной геометрии листа (verified surface/winding), + сравнение
«тот же регион без B1». Никакого нейроинференса. Никаких десятков GB.

---

## 0. Ключевой факт, на котором стоит план

Для **PHercParis4** три ингредиента существуют в **одном** координатном пространстве — объём
`20260411134726` (2.4µm 78keV, сетка (z,y,x) = [75784, 32693, 32693], воксель 2.4µm):

1. сырой CT (тот же объём);
2. официальное fiber prediction (`representations/predictions/fibers/`, привязано к `20260411134726`);
3. 70 проверенных surface-сегментов (`segments/2026*-{wNNN-*|...}`, `original_volume_id = 20260411134726`)
   + winding-аннотации (`spiral_datasets/PHercParis4/`).

Межскановая регистрация не нужна. (Отметено: наш прежний план с NML-кубами 7.91µm остаётся
единственным путём к волокно-уровневой цифре — через инференс fiber_hz_vt на held-out кубе; это
отдельное последующее решение.)

## 1. Выбранный регион (ФИНАЛ по ПОЛНОМУ GT-набору, 65/65 волокон)

**Регион** (окно с максимумом eval-волокон по полному GT):
```
базовые воксели 2.4µm (x,y,z):  x[16384..18432]  y[9216..11264]  z[44544..46592]
level-3 воксели (19.2µm):       x[2048..2304)    y[1152..1408)   z[5568..5824)   (256³)
чанки prediction (64³):         cx 32..35        cy 18..21       cz 87..90       (4×4×4)
чанки CT 128³ (тот же L3-грид): cx 16..17        cy 9..10        cz 43..45
```

**GT в регионе: 10 eval-волокон, 2199 GT-точек** (полный набор: 65/65 файлов, 155,774 точек).
**Same-space доказано количественно по полному GT:** presence в точках GT-волокон 216.2/255
(93% точек ≥64) против глобального среднего региона 18.2 и сдвинутого контроля 16.7±4.6 (~45σ).
6 из 7 крупных волокон идут по предсказанию (190–251); fiber `000026` (mean 24.6) — волокно,
которое детектор почти не видит (реальный failure mode, вошедший в бенчмарк).

**Скачано и собрано (2026-09-26):** `data/pred/region_{presence,nx,ny}.npy` (256³ uint8 каждый;
presence 44.7% nonzero), `data/ct/region_ct.npy`, `data/spiral/eval_fibers/*.json` (65/65 ✅),
`data/spiral/{abs_winding,relative_windings,umbilicus}.json`.

## 2. Инвентарь файлов (URL, размер, формат, назначение, обязательность)

### 2.1 Fiber prediction — S3 (быстрый хост), слой 20260915 (лучшая модель: checkpoint
`best_ema_0p999.pt`, test loss 0.208 против 0.903 у слоя 20260801)

Базовый префикс:
```
https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/representations/predictions/fibers/20260411134726-fibers-20260915212757-L1/
```

| Файл (суффикс канала/уровня/чанка) | Размер | Формат | Для чего | Обязателен |
|---|---|---|---|---|
| `PHercParis4-20260411134726-las-sd1-7ff0ce6c_presence.ome.zarr/3/{cz}/{cy}/{cx}`, cz 72–75, cy 29–32, cx 29–32 | 64 чанка × 80–130KB ≈ **6–8 MB** | zarr v2, uint8, blosc-zstd, sep `/` | поле присутствия волокна → маска → скелетизация → фрагменты | **ДА** |
| `..._nx.ome.zarr/3/{...}` те же 64 чанка | ≈ **16 MB** (чанк ~250KB) | uint8 | компонент направления (для сравнения с нашим тангенсом; B1 не меняется) | да |
| `..._ny.ome.zarr/3/{...}` те же 64 чанка | ≈ **16 MB** | uint8 | второй компонент направления | да |
| `.../inference.json` | ~30 KB | JSON | provenance (модель, чекпойнт, уровни, shapes) | да |
| `.../PHercParis4-20260411134726-las-sd1-7ff0ce6c.lasagna.json` | 705 B | JSON | указатель zarr-групп (base_shape) | да |

**Не** скачиваем: уровень 4 (грубее), слой 20260801, полные пирамиды, остальные 4 свитка.

### 2.2 CT-контекст — S3, тот же объём, уровень 3 (та же сетка 19.2µm, что prediction)

| Файл | Размер | Формат | Для чего | Обязателен |
|---|---|---|---|---|
| `PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/3/{cz}/{cy}/{cx}` | 18 чанков × 2048KB = **36 MB** | zarr v2, uint8, БЕЗ компрессора, **чанки 128³** (индексы cz 36–37, cy 14–16, cx 14–16 — НЕ как у prediction!) | визуальная проверка, контекст (не участвует в алгоритме). Скачано 2026-09-26 | опционально |

### 2.3 Известная геометрия листа (GT) — два источника

**(a) Сегмент w120-121 (surface_tracing, проверенный лист)** — S3:
```
PHercParis4/segments/20260623165742-w120-121/mesh/20260623165742-on-20260411134726-2.4um.tifxyz/
  meta.json  404 B     — bbox, scale, формат
  x.tif      66,158,278 B  \  float32-сетки 6797×2427 (шаг ~12.5µm),
  y.tif      66,158,278 B   > позиции поверхности в базовых вокселях
  z.tif      66,158,278 B  /  2.4µm-объёма (downscale-4 сетка)
```
Итого **~198.6 MB** — самый тяжёлый элемент. Назначение: расстояние «коннектор ↔ известный лист»
(критерий хорошо/плохо из брифа). **Обязателен для sheet-level оценки** (или заменяется (b)).
Соседние листы w118-119 / w122-123 (+198.6 MB каждый) — НЕ качаем в минимуме; cross-sheet тест
сначала делаем как «уход коннектора от поверхности w120-121 дальше порога межвиткового зазора».

**(b) `eval_fibers` из spiral_datasets** — dl.ash2txt.org (медленный, рвёт соединения — качать только
resumable-скриптом):
```
https://dl.ash2txt.org/datasets/spiral_datasets/PHercParis4/eval_fibers/anon_20260815T*.json
```
**ВЕРИФИЦИРОВАНО (2026-09-26): это волокно-уровневый GT в пространстве предсказания.** 65 файлов
(~230 KB каждый, итого ~15 MB). Формат — VC3D fiber JSON (`type: "vc3d_fiber"`,
`optimization_mode: "native_fiber_trace3d"`): `control_points` (анкерные точки) + `line_points`
(плотная полилиния, ~2500 точек), координаты в `vc_open_data_coordinate_space:
"PHercParis4/20260411134726@L0"` — уровень 0 того же объёма, что и prediction. Порядок осей
позиций: (x, y, z), третья координата = длинная ось свитка (до ~68k < 75784). Это**главный
scoring-источник**: proposed link классифицируется как true/false по принадлежности концов одному
eval-волокну — тот же протокол, что в синтетическом бенчмарке, но на реальных данных.

**(c) Winding-аннотации** — spiral_datasets, крошечные:
| Файл | Размер | Назначение | Обязателен |
|---|---|---|---|
| `abs_winding.json` | 20 KB | абсолютные номера витков | да |
| `relative_windings.json` | 773 KB | относительная_adjacency листов (кто сосед w120-121) | да |
| `same_windings.json` | 1.7 MB | группы одинаковых витков | опционально |
| `umbilicus.json` | 12 KB | ось свитка (позиционирование/проверки) | опционально |

## 3. Итоговый минимальный набор скачивания

| Шаг | Что | Объём |
|---|---|---|
| 1 (сейчас) | presence 64 чанка + nx 64 + ny 64 + 2 маленьких JSON'а предсказания | **~40–55 MB** |
| 2 (сейчас) | spiral_datasets JSON'ы (abs_winding, relative_windings, umbilicus, 1×eval_fiber) | **~1 MB** |
| 3 (сейчас, опционально) | CT уровень 3, 8 чанков 2×2×2 | **2 MB** |
| 4 (решение после inspecии eval_fibers) | сегментный tifxyz w120-121 | **~199 MB** (или отложить, если eval_fibers покрывают) |

Итого до запуска B1: **~45–60 MB**; худший случай с полным tifxyz: **~260 MB**.

## 4. Команды скачивания (Windows / Git Bash)

### Шаг 1–2: fiber prediction чанки (S3, быстрый хост)
```bash
cd "C:/Users/Sb/Desktop/elder scrolls"
BASE="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/representations/predictions/fibers/20260411134726-fibers-20260915212757-L1"
mkdir -p data/pred/{presence,nx,ny}/3
for ch in presence nx ny; do
  for cz in 72 73 74 75; do for cy in 29 30 31 32; do for cx in 29 30 31 32; do
    curl -sS --retry 3 -o "data/pred/$ch/3/${cz}_${cy}_${cx}.chunk" \
      "$BASE/PHercParis4-20260411134726-las-sd1-7ff0ce6c_${ch}.ome.zarr/3/${cz}/${cy}/${cx}"
  done; done; done
done
curl -sS -o data/pred/inference.json "$BASE/inference.json"
curl -sS -o data/pred/lasagna.json "$BASE/PHercParis4-20260411134726-las-sd1-7ff0ce6c.lasagna.json"
```
Декодирование чанков (blosc-zstd) — `pip install numcodecs`, сборка в numpy-куб 256³ —
мини-скриптом на следующем шаге (после проверки данных, как согласовано).

### Шаг 2: spiral_datasets JSON (медленный хост — ТОЛЬКО resumable)
```bash
cd "C:/Users/Sb/Desktop/elder scrolls"
BASE="https://dl.ash2txt.org/datasets/spiral_datasets/PHercParis4"
mkdir -p data/spiral
fetch () { for i in $(seq 1 400); do
  curl -sS --max-time 60 --speed-limit 500 --speed-time 15 -C - -o "$2" "$1" && return 0; sleep 1
done; }
fetch "$BASE/abs_winding.json" data/spiral/abs_winding.json
fetch "$BASE/relative_windings.json" data/spiral/relative_windings.json
fetch "$BASE/umbilicus.json" data/spiral/umbilicus.json
fetch "$BASE/eval_fibers/anon_20260815T014816946_000002.json" data/spiral/eval_fiber_000002.json
```

### Шаг 3 (опционально): CT уровень 3
```bash
CT="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/volumes/20260411134726-2.400um-0.2m-78keV-masked.zarr/3"
mkdir -p data/ct/3
for cz in 72 73; do for cy in 29 30; do for cx in 29 30; do
  curl -sS --retry 3 -o "data/ct/3/${cz}_${cy}_${cx}.chunk" "$CT/${cz}/${cy}/${cx}"
done; done; done
```

### Шаг 4 (если понадобится): сегментный tifxyz w120-121
```bash
SEG="https://vesuvius-challenge-open-data.s3.us-east-1.amazonaws.com/PHercParis4/segments/20260623165742-w120-121/mesh/20260623165742-on-20260411134726-2.4um.tifxyz"
mkdir -p data/seg_w120-121
for f in meta.json x.tif y.tif z.tif; do
  curl -sS --retry 3 -o "data/seg_w120-121/$f" "$SEG/$f"
done
```

## 5. Что НЕ скачиваем и почему

- Уровень 4 предсказания (38.4µm — грубее нужного) и слой 20260801 (хуже по test loss).
- Соседние сегменты w118-119/w122-123 (tifxyz) — до тех пор, пока не понадобится точный вердикт
  «на какой именно соседний виток прыгнул ложный коннектор».
- Полные пирамиды CT, 45µm/1.129µm сканы, ink-detection, surface-renders.
- Fiber predictions других свитков (PHerc0139/0332/1299/1451) — тот же класс данных, Paris4 достаточен.

## 6. Статус открытых вопросов (обновлено 2026-09-26)

1. **Формат `eval_fibers/anon_*.json`** — РЕШЕНО: VC3D fiber JSON, волокно-уровневый GT в
   координатах 20260411134726@L0, порядок осей (x,y,z). 65 файлов качаются параллельным
   resumable-фетчером (`fetch_eval_parallel.sh`).
2. **Порядок осей** в bbox/tifxyz позициях: третья ось = длинная (z-скана) — подтверждено и на
   bbox'ах сегментов, и на координатах eval-волокон (pos2 до ~68k < 75784). Первые две оси
   (x,y vs y,x) фиксируются численно при сопоставлении с presence-полем.
3. **uint8 → вероятность**: presence/nx/ny — uint8. Реальные статистики получены (§1);
   порог маски выбирается по отделимости фон/волокно на гистограмме — при построении фрагментов.
4. **Соответствие регион ↔ GT**: регион 256³ сдвигается туда, где проходит больше всего
   eval-волокон (GT-driven); prediction/CT чанки докачиваются точечно под выбранный регион.
5. **Наблюдение**: у Vesuvius есть межскановые отображения сегментов (`mesh/...-on-20230205180739-
   7.91um.tifxyz` рядом с on-20260411134726) — на будущее, если понадобится связка с 7.91µm GT.
