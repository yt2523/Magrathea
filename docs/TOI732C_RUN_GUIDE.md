# TOI-732 c：手动运行当前测试版本

本分支的科学入口只有三个Python文件：`run/scan_compositions.py`生成配置，`run/execute_scan.py`执行与检查，`run/plot_compositions.py`只读作图。C++积分/EOS仍在src。AI编程记录、归档和合成测试不是运行前置依赖；运行入口不调用AI。

**这是350K/.1bar/100bar测试热结构的可重复版本，不是正式TP或最终组成后验。** 主有水EOS为AQUA公用轴子表；旧拼接仅历史有限对照。扫描器当前限定无外部TP的`gas_hhe_iso_adiabatic100`，会拒绝偷偷加入TP文件/换selector。外部TP单例接口在原生程序中保留，见stageB报告。

## 1. 在WSL构建

已有Ubuntu、g++、make与GSL环境中，从仓库目录运行。强制重编，不复用旧.o缓存。

```bash
cd /mnt/d/Codex/downloads/subneptune-research-workflow
repo=$(pwd)
make -B -j2
objects=()
for object in src/*.o; do
  if [ "$object" != src/main.o ]; then objects+=("$object"); fi
done
g++ -std=c++11 -O3 -Wall -I. -Isrc tests/native_hhe_control_audit.cpp "${objects[@]}" -lgsl -lgslcblas -lm -o native_audit
g++ -std=c++11 -O3 -Wall -I. -Isrc tests/native_water_audit.cpp "${objects[@]}" -lgsl -lgslcblas -lm -o native_water_audit
```

两个审计器是普通C++程序：一个包装正向计算，另一个按保存的P/T/物相重算密度与梯度。它们不是AI工具。独立密度相符只证明保存状态一致，不等于所有ODE终止码/物理稳定性均已认证。

## 2. 准备独立表格目录

新目录全放D盘；示例目录名若存在应换新名字。原始`tabulated/AQUA.txt`不覆盖。压缩子表是原表逐行保留T≤50000K的确切字节，实际最高48978K，修复的是共用坐标轴适用范围，未编辑EOS数值。

```bash
backend=/mnt/d/Codex/downloads/toi732c-my-backend-20261113
if [ -e "$backend" ]; then echo 'Choose a new backend directory'; exit 1; fi
mkdir -p "$backend"
cp -R "$repo/tabulated" "$backend/tabulated"
gzip -dc "$repo/input/toi732c-test/aqua-commonaxis.txt.gz" > "$backend/tabulated/AQUA.txt"
sha256sum "$backend/tabulated/AQUA.txt"
```

解压后应为`c493e0fb214bef945dacb3abf076c4f11b8c27b58aa9d174c293947236db5768`。子表出处/边界与原表SHA见同目录manifest；引用Haldemann等2020 DOI10.1051/0004-6361/202038367，并保留原仓库许可。

## 3. 先运行一点，再续跑质量向量

`input/toi732c-test/three-mass-example.json`有三个质量和三种组成，共9次。JSON可编辑，四分数顺序固定Fe/硅酸盐/H2O/HHe；.01表示1%，不是百分数字1。原生层质量由分数乘M计算。模板中的350K、P_surface=100000 dyn/cm²（=.1bar）、100bar热分界均为测试假设。

```bash
campaign=/mnt/d/Codex/downloads/toi732c-my-scan-20261113
python3 "$repo/run/scan_compositions.py" --generate "$repo/input/toi732c-test/three-mass-example.json" "$campaign"
python3 "$repo/run/execute_scan.py" "$campaign" --backend "$backend" --solver "$repo/native_audit" --checker "$repo/native_water_audit" --target-radius 2.39 --max-launches 1 --timeout 180 --stop-after-failures 3
```

第一点检查通过后，使用同一条命令把`--max-launches 1`改为9，终态点会跳过。再运行一次不会多启动模型。目标半径只进入结果残差，不传入原生配置；模型R不被强设2.39。

每点保存run.cfg、model.dat、runtime.json、checked.csv和日志；总览为summary.csv，账本execution.json。FAILED点保留，不自动重试；连续3个新失败暂停。配置/程序/表/产物被改、旧产物混入或RUNNING中断会要求先检查。不要删除失败文件来伪造续跑；另建新目录开展有明确修改的新实验。

本次核验了发布入口的9配置生成及已有96点的零新增启动续跑；204次实际任务计算使用同源码B17审计二进制和同一子表，结果与哈希在交付档案中。没有为了包装重算历史网格。

## 4. 只重画本轮结果

原始数据和三图见`research/composition-constraints-20261112/delivery`。最终拟合使用150个正向点；25个离轨/边缘验证点不进入拟合。以下Windows PowerShell命令使用本机已有NumPy2.2.6、Matplotlib3.10.3、SciPy1.15.3；不启动求解器。需新输出目录。

```powershell
Set-Location D:/Codex/downloads/subneptune-research-workflow
$env:TEMP='D:/Codex/tmp'
$env:TMP='D:/Codex/tmp'
$env:MPLCONFIGDIR='D:/Codex/tmp/matplotlib'
$python='C:/Users/PC/AppData/Local/Programs/Python/Python312/python.exe'
& $python -B run/plot_compositions.py --summaries research/composition-constraints-20261112/delivery/data/final-fit.csv --out D:/Codex/downloads/toi732c-my-figures-20261113 --radius 2.39 --radius-minus .11 --radius-plus .10 --central-mass 8.04 --phase-groups research/composition-constraints-20261112/delivery/data/water-boundary-diagnostic-v2.json --interpolation track-pchip
```

输出三类PNG/矢量PDF和analysis.json。灰色是中心质量可评估域，白色未评估不等于排除。相态JSON用于阻止跨外水边界组插值；不能把旧JSON当新模型的相态结果。默认linear-tri保留为粗对照，严禁省略精度说明后当最终论文曲线。

本轮6个新中心线检查最大误差.00311R⊕，但12个边缘检查仍达.01142；三质量包络依赖连续分段线性假设与矩形观测框，不是后验/联合68%区。新质量、组成、TP或热参数需要新单例与局部验证，不能用旧误差作为全域上界。

## 文件位置

- 主C++：src；气层TP插值：src/tp_profile.cpp；有限域起始括区：src/radius_bracket.h。
- 用户运行入口：run下三个新文件；小示例/确切EOS子表：input/toi732c-test。
- 数值结果、原始产物ZIP、独立验收和协作交接：research/composition-constraints-20261112。
- [本轮结果与代码原理](../research/composition-constraints-20261112/delivery/README.md)。此处停止计算，不自动续开网格。
