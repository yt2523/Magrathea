# MAGRATHEA 剖面对照绘图

`compare_profiles.py` 接收一个或多个 mode-0 剖面文件，输出一张含四幅曲线的图：密度、压强、温度、包围质量随半径的变化；另外自动输出一张独立 T–P 剖面图。只读取原始数据，不会运行行星求解器，也不修改 `.cfg` 或原始结果。

## 在当前 Ubuntu 终端使用

从项目目录运行：

```bash
cd /mnt/d/GPT/projects/Sub-Neptune/Magrathea

# 今天亲手运行的两个结果
bash plot/compare_profiles.sh \
  ../outputs/my-practice-20261019/run01.txt \
  ../outputs/my-practice-20261019/run02.txt \
  -o ../outputs/my-practice-20261019/my-temperature-comparison.png

# 单个行星也能画
bash plot/compare_profiles.sh \
  ../outputs/my-practice-20261019/run02.txt \
  -o ../outputs/my-practice-20261019/single-planet.png

# 之前的不同构成：干燥岩石、30%水、90%水、1% H/He
bash plot/compare_profiles.sh \
  ../outputs/literature-cases-20261018/profiles/rock_reference.txt \
  ../outputs/literature-cases-20261018/profiles/water30.txt \
  ../outputs/literature-cases-20261018/profiles/water90.txt \
  ../outputs/literature-cases-20261018/profiles/gasdwarf_1pct.txt \
  --labels dry_rock water30 water90 HHe1pct \
  --log-pressure \
  -o ../outputs/my-practice-20261019/composition-comparison.png
```

需要更多星球，就在 `-o` 前继续添加结果文件路径；文件名有空格时用双引号包住。`--labels` 可省略，默认使用文件名；提供时每个文件必须对应一个名称。输出支持 `.png`、`.pdf`、`.svg`，同名图会更新，原始剖面不会改变。

原调用方式不变。若 `-o` 指定 `comparison.png`，独立 T–P 图会保存为 `comparison_tp.png`；PDF/SVG 同理。T–P 横轴是温度 K，纵轴是压强 bar，采用对数刻度，压强向下增大。曲线覆盖文件中保存的整个内部剖面，包含固态内部；它不只代表大气。非正压强点不显示，并中断曲线。该图固定采用对数压强，不受 `--log-pressure` 开关影响。

`compare_profiles.sh` 优先使用 Ubuntu 已有的 NumPy/Matplotlib；当前电脑 Ubuntu 没有这些库时，会调用已有的 Windows Python 3.12 画图。不下载软件，不安装依赖，也不改变 Ubuntu 的求解环境。在其他电脑可设置 `MAGRATHEA_WINDOWS_PYTHON` 指向 WSL 可执行的 Windows Python 路径。

Windows 后备方式适用于当前 D 盘目录及 `/mnt/盘符/...` 路径；Ubuntu 自有的 `/home/...` 路径不在此转换范围，需改用具备绘图库的 Ubuntu Python。当前这批结果都在 D 盘，已实际测试。

## 普通 Python 用法

如果当前 Python 已有 NumPy 和 Matplotlib，可直接运行：

```text
python plot/compare_profiles.py 文件1.txt 文件2.txt -o 对照图.png
```

VS Code 可以用「文件 → 打开文件」打开生成的 PNG；也可以将 PNG 拖入编辑器预览。以后每跑完一组新模型，重新调用绘图入口即可。

## 读图

- 横轴是离中心的真实半径，单位地球半径 R⊕；没有把每个行星的半径分别归一到 1。曲线右端因此体现行星大小。
- 左上：密度。陡降可出现在核幔等组成边界，也可来自同一层内的物相转变，不能只凭密度跳变判定组成。
- 右上：压强，单位 GPa。`--log-pressure` 可观察跨越许多数量级的气层压强；零压强点在对数图中不显示。
- 左下：温度，单位 K。表面温度相同也不意味着内部温度相同；内部曲线取决于热结构与 EOS。
- 右下：该半径内累计包含的质量，单位 M⊕，不是局部密度。右端是总质量。
- 图例列出从每个结果文件末行读到的总质量、半径、表面温度与表面压强，避免把不同边界条件当成同一实验。1 GPa = 10000 bar。

## 已有案例的区别

你今天的 run01/run02 是同一组成、不同表面温度的对照：核 0.325 M⊕、幔 0.675 M⊕、无水和气，表面压强 0.1 bar。之前文献案例的模型设置如下（质量比例）：

|文件|总质量/M⊕|水|H/He|表面温度/K|表面压强/bar|
|---|---:|---:|---:|---:|---:|
|rock_reference|8.04|0|0|300|1|
|water30|8.04|30%|0|300|1|
|water90|8.04|90%|0|300|1|
|gasdwarf_1pct|8.04|0|1%|360|0.05|

前三者剩余岩石的铁核/硅酸盐比为 1:2；气体案例的剩余岩石按 0.325:0.675 划分。因此气体案例还改变了核幔比和热边界，不能将全部半径差异单独归因于气体。

这些案例仍是文献配方试算，完整设置及问题说明见 `../experiments/archive/20261018/literature-cases/README.md`。本次图未采用被标记的原 0.05 bar 蒸汽试算。绘图不会判断 EOS 选支是否物理合理，也无法从普通输出读到未保存的求解器状态。输出表数字经过舍入，图例半径不能作为额外的高精度解。

输入必须是单个行星的剖面表；批量质量-半径表、MCMC 样本表不适用。若同一文件出现多个 `Index` 表头，脚本会报 appended runs，需先拆分文件；它不会静默合并多次运行。

## 维护检查

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s plot -p test_compare_profiles.py
```

解析器检查覆盖空行与带空格的相名、重复追加、缺失表头、非有限数、逆序半径、错误数字和空剖面。已用当前两份实测结果、单个结果及四个不同构成结果验证生成图像。
