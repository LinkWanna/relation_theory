## 关系理论

这个仓库包含了一些我在学习数据库时，针对**关系数据理论**这个章节中的各种概念和算法所编写的代码实现。主要内容包括：
1. 关系模式（Relation Schema）的表示
2. 求属性关于函数依赖集的闭包（Attribute Closure）
3. 计算候选键（Candidate Keys）
4. 求最小函数依赖集（Minimal Cover）
5. 关系模式的范式判断（Normalization），包括1NF, 2NF, 3NF, BCNF
6. 判断关系模式的分解（Decomposition）是否为无损连接（Lossless Join）


### Usage

代码主要使用Python编写，依赖于标准库。可以通过以下方式使用：

```python
from relation_theory import RelationSchema

rs = RelationSchema.from_str("ABCDE", ["A->C", "BC->D", "D->B", "C->E"])
print(rs)
keys = rs.candidate_keys()  # 获取候选键
print("Candidate Keys:", keys)
level, violations = rs.judge_NF()  # 判断范式等级
print("Normal Form Level:", level)
print("Violations:", violations)

sub_schemas = [{"B", "C", "D"}, {"A", "C", "E"}]
is_fd_preserving = rs.is_fd_preserving_decomposition(sub_schemas)  # 判断保持函数依赖分解
is_lossless = rs.is_lossless_decomposition(sub_schemas)  # 判断无损分解

print("Is FD Preserving Decomposition:", is_fd_preserving)
print("Is Lossless Decomposition:", is_lossless)

# 分解 ρ 保持函数依赖
rs_3NF = rs.decompose_into_3NF()
print("3NF Decomposition:", rs_3NF)

is_fd_preserving_3NF = rs.is_fd_preserving_decomposition(rs_3NF)
is_lossless_3NF = rs.is_lossless_decomposition(rs_3NF)

print("Is 3NF Decomposition FD Preserving:", is_fd_preserving_3NF)
print("Is 3NF Decomposition Lossless:", is_lossless_3NF)

```
