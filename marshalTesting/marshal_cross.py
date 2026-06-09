"""
Marshal Module Stability and Correctness Test Suite

测试目标:
1. 确定性: 同一对象在同一版本下多次 marshal 是否产生完全相同的结果
2. 边界条件测试: 浮点数、递归结构、大集合等
3. 模糊测试: 随机生成对象测试

测试方法:
- 黑盒: 等价划分、边界值分析、随机测试
- 白盒: 基于 marshal.c 的实现进行路径覆盖测试
"""

import marshal
import hashlib
import math
import os
import random
import sys
import time
import platform
from datetime import datetime
from typing import Any, Dict, List, Tuple

# =====================================================
# 测试配置
# =====================================================

# 测试次数（用于确定性测试）
DETERMINISM_ITERATIONS = 10

# 随机测试数量
FUZZ_TEST_COUNT = 100

# 递归深度限制
MAX_RECURSION_DEPTH = 100


# =====================================================
# 1. 确定性测试
# =====================================================

def test_determinism() -> Dict[str, Any]:
    """
    测试同一对象在同一版本下多次 marshal 是否产生相同的字节流
    
    预期: 所有测试用例的多次 marshal 结果应该完全相同
    """
    print("\n" + "=" * 70)
    print("1. 确定性测试 - 同一版本多次 Marshal 是否产生相同结果")
    print("=" * 70)
    
    test_cases = _get_determinism_test_cases()
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test_name, obj in test_cases:
        print(f"\n测试: {test_name}")
        
        # 多次序列化，比较哈希
        hashes = []
        sizes = []
        
        for i in range(DETERMINISM_ITERATIONS):
            try:
                data = marshal.dumps(obj)
                h = hashlib.sha256(data).hexdigest()
                hashes.append(h)
                sizes.append(len(data))
            except Exception as e:
                results["failed"] += 1
                results["details"].append({
                    "test": test_name,
                    "status": "ERROR",
                    "error": str(e)
                })
                print(f"  ✗ 错误: {e}")
                break
        else:
            # 所有迭代都成功
            unique_hashes = set(hashes)
            unique_sizes = set(sizes)
            
            if len(unique_hashes) == 1 and len(unique_sizes) == 1:
                results["passed"] += 1
                results["details"].append({
                    "test": test_name,
                    "status": "PASS",
                    "hash": hashes[0],
                    "size": sizes[0]
                })
                print(f"  ✓ 通过: {DETERMINISM_ITERATIONS} 次结果一致")
                print(f"    哈希: {hashes[0][:16]}...")
                print(f"    大小: {sizes[0]} 字节")
            else:
                results["failed"] += 1
                results["details"].append({
                    "test": test_name,
                    "status": "FAIL",
                    "unique_hashes": len(unique_hashes),
                    "unique_sizes": len(unique_sizes)
                })
                print(f"  ✗ 失败: 产生 {len(unique_hashes)} 种不同的哈希")
    
    print(f"\n确定性测试结果: {results['passed']}/{len(test_cases)} 通过")
    return results


def _get_determinism_test_cases() -> List[Tuple[str, Any]]:
    """获取确定性测试用例"""
    test_cases = []
    
    # 基础类型
    basic_cases = [
        ("None", None),
        ("True", True),
        ("False", False),
        ("Zero", 0),
        ("SmallInt", 42),
        ("LargeInt", 2**100),
        ("NegativeInt", -12345),
        ("Float", 3.14159),
        ("String", "hello world"),
        ("EmptyString", ""),
        ("Unicode", "你好世界 🌍"),
        ("Bytes", b"hello"),
        ("EmptyBytes", b""),
        ("Complex", 1+2j),
    ]
    test_cases.extend(basic_cases)
    
    # 容器类型
    container_cases = [
        ("EmptyList", []),
        ("List", [1, 2, 3, 4, 5]),
        ("NestedList", [1, [2, [3, [4]]]]),
        ("EmptyTuple", ()),
        ("Tuple", (1, 2, 3)),
        ("SingletonTuple", (1,)),
        ("EmptyDict", {}),
        ("Dict", {"a": 1, "b": 2, "c": 3}),
        ("NestedDict", {"a": {"b": {"c": 1}}}),
        ("EmptySet", set()),
        ("Set", {1, 2, 3}),
        ("EmptyFrozenSet", frozenset()),
        ("FrozenSet", frozenset([1, 2, 3])),
    ]
    test_cases.extend(container_cases)
    
    # 浮点数特殊情况
    float_cases = [
        ("FloatZero", 0.0),
        ("FloatNegZero", -0.0),
        ("FloatInf", float("inf")),
        ("FloatNegInf", float("-inf")),
        ("FloatNaN", float("nan")),
        ("FloatEpsilon", 2.2250738585072014e-308),
        ("FloatMax", 1.7976931348623157e+308),
    ]
    test_cases.extend(float_cases)
    
    return test_cases


# =====================================================
# 2. 递归/循环引用测试
# =====================================================

def test_recursive_structures() -> Dict[str, Any]:
    """
    测试递归和循环引用结构的 marshal 行为
    """
    print("\n" + "=" * 70)
    print("2. 递归/循环引用测试")
    print("=" * 70)
    
    test_cases = _get_recursive_test_cases()
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test_name, obj in test_cases:
        print(f"\n测试: {test_name}")
        
        try:
            data = marshal.dumps(obj)
            restored = marshal.loads(data)
            
            if _check_cyclic_structure(obj, restored):
                results["passed"] += 1
                size = len(data)
                results["details"].append({
                    "test": test_name,
                    "status": "PASS",
                    "size": size
                })
                print(f"  ✓ 通过: 成功序列化 {size} 字节")
            else:
                results["failed"] += 1
                print(f"  ✗ 失败: 序列化后结构不匹配")
                
        except Exception as e:
            results["failed"] += 1
            print(f"  ✗ 错误: {e}")
    
    print(f"\n递归结构测试结果: {results['passed']}/{len(test_cases)} 通过")
    return results


def _get_recursive_test_cases() -> List[Tuple[str, Any]]:
    """获取递归/循环引用测试用例"""
    test_cases = []
    
    # 自引用列表
    self_list = []
    self_list.append(self_list)
    test_cases.append(("SelfReferentialList", self_list))
    
    # 自引用字典
    self_dict = {}
    self_dict["self"] = self_dict
    test_cases.append(("SelfReferentialDict", self_dict))
    
    # 双向引用
    a = []
    b = [a]
    a.append(b)
    test_cases.append(("MutualReference", a))
    
    # 三元循环
    x = []
    y = []
    z = []
    x.append(y)
    y.append(z)
    z.append(x)
    test_cases.append(("TripleCycle", x))
    
    # 元组中的循环
    cycle_tuple = ()
    lst = [cycle_tuple]
    cycle_tuple = (lst,)
    lst[0] = cycle_tuple
    test_cases.append(("CycleInTuple", cycle_tuple))
    
    # 字典中的循环
    cycle_dict = {}
    lst = [cycle_dict]
    cycle_dict["list"] = lst
    test_cases.append(("CycleInDict", cycle_dict))
    
    # 深层递归列表
    deep = []
    current = deep
    for i in range(MAX_RECURSION_DEPTH):
        current.append([])
        current = current[-1]
    test_cases.append((f"DeepRecursion_{MAX_RECURSION_DEPTH}", deep))
    
    return test_cases


def _check_cyclic_structure(obj1, obj2, visited=None, depth=0) -> bool:
    """检查两个循环引用结构是否等价"""
    if depth > 500:
        return True
    
    if visited is None:
        visited = set()
    
    obj_id = id(obj1)
    if obj_id in visited:
        return True
    visited.add(obj_id)
    
    if type(obj1) != type(obj2):
        return False
    
    if isinstance(obj1, (list, tuple)):
        if len(obj1) != len(obj2):
            return False
        for i in range(len(obj1)):
            if not _check_cyclic_structure(obj1[i], obj2[i], visited, depth + 1):
                return False
        return True
    
    if isinstance(obj1, dict):
        if set(obj1.keys()) != set(obj2.keys()):
            return False
        for k in obj1:
            if not _check_cyclic_structure(obj1[k], obj2[k], visited, depth + 1):
                return False
        return True
    
    try:
        if isinstance(obj1, float) and isinstance(obj2, float):
            if math.isnan(obj1) and math.isnan(obj2):
                return True
            if math.isinf(obj1) and math.isinf(obj2):
                return math.copysign(1, obj1) == math.copysign(1, obj2)
        return obj1 == obj2
    except:
        return repr(obj1) == repr(obj2)


# =====================================================
# 3. 边界值测试
# =====================================================

def test_boundary_values() -> Dict[str, Any]:
    """
    边界值测试 - 基于等价划分和边界值分析
    """
    print("\n" + "=" * 70)
    print("3. 边界值测试")
    print("=" * 70)
    
    test_cases = _get_boundary_test_cases()
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test_name, obj in test_cases:
        print(f"\n测试: {test_name}")
        
        try:
            data = marshal.dumps(obj)
            restored = marshal.loads(data)
            
            if _safe_compare(obj, restored):
                results["passed"] += 1
                size = len(data)
                print(f"  ✓ 通过: {size} 字节")
            else:
                results["failed"] += 1
                print(f"  ✗ 失败: 值不匹配")
                
        except Exception as e:
            results["failed"] += 1
            print(f"  ✗ 错误: {e}")
    
    print(f"\n边界值测试结果: {results['passed']}/{len(test_cases)} 通过")
    return results


def _get_boundary_test_cases() -> List[Tuple[str, Any]]:
    """获取边界值测试用例"""
    test_cases = []
    
    # 整数边界
    int_boundaries = [
        ("IntMinus1", -1),
        ("Int0", 0),
        ("Int1", 1),
        ("Int2_31_Minus1", 2**31 - 1),
        ("IntNeg2_31", -(2**31)),
        ("Int2_31", 2**31),
        ("Int2_63_Minus1", 2**63 - 1),
        ("IntNeg2_63", -(2**63)),
        ("Int2_63", 2**63),
        ("Int2_1000", 2**1000),
    ]
    test_cases.extend(int_boundaries)
    
    # 字符串边界
    string_boundaries = [
        ("StringEmpty", ""),
        ("String1Char", "a"),
        ("String255", "a" * 255),
        ("String256", "a" * 256),
        ("String65535", "a" * 65535),
        ("String65536", "a" * 65536),
        ("StringUnicode1", "中"),
        ("StringUnicode1000", "中" * 1000),
    ]
    test_cases.extend(string_boundaries)
    
    # 列表边界
    list_boundaries = [
        ("ListEmpty", []),
        ("List1Elem", [1]),
        ("ListLarge", list(range(10000))),
    ]
    test_cases.extend(list_boundaries)
    
    # 字典边界
    dict_boundaries = [
        ("DictEmpty", {}),
        ("Dict1Elem", {"a": 1}),
        ("DictLarge", {str(i): i for i in range(1000)}),
    ]
    test_cases.extend(dict_boundaries)
    
    # 元组边界
    tuple_boundaries = [
        ("TupleEmpty", ()),
        ("Tuple1Elem", (1,)),
        ("TupleLarge", tuple(range(10000))),
    ]
    test_cases.extend(tuple_boundaries)
    
    return test_cases


def _safe_compare(a, b, depth=0) -> bool:
    """安全比较两个对象"""
    if depth > 500:
        return True
    
    if a is b:
        return True
    
    if type(a) != type(b):
        return False
    
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True
        if math.isinf(a) and math.isinf(b):
            return math.copysign(1, a) == math.copysign(1, b)
    
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False
        return all(_safe_compare(x, y, depth + 1) for x, y in zip(a, b))
    
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            return False
        return all(_safe_compare(a[k], b[k], depth + 1) for k in a)
    
    if isinstance(a, (set, frozenset)):
        if len(a) != len(b):
            return False
        return all(any(_safe_compare(x, y, depth + 1) for y in b) for x in a)
    
    return a == b


# =====================================================
# 4. 模糊测试 (Fuzzing)
# =====================================================

def test_fuzzing() -> Dict[str, Any]:
    """
    模糊测试 - 随机生成各种类型的对象进行测试
    """
    print("\n" + "=" * 70)
    print(f"4. 模糊测试 - {FUZZ_TEST_COUNT} 个随机对象")
    print("=" * 70)
    
    random.seed(42)
    
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for i in range(FUZZ_TEST_COUNT):
        obj = _generate_random_object(max_depth=3)
        
        print(f"\r测试: {i+1}/{FUZZ_TEST_COUNT}", end="", flush=True)
        
        try:
            data = marshal.dumps(obj)
            restored = marshal.loads(data)
            
            if _safe_compare(obj, restored):
                results["passed"] += 1
            else:
                results["failed"] += 1
                print(f"\n  ✗ 失败: Fuzz_{i+1}")
        except Exception as e:
            results["failed"] += 1
            print(f"\n  ✗ 错误: Fuzz_{i+1} - {e}")
    
    print(f"\n\n模糊测试结果: {results['passed']}/{FUZZ_TEST_COUNT} 通过")
    return results


def _generate_random_object(max_depth: int = 3) -> Any:
    """递归生成随机对象"""
    if max_depth <= 0 or random.random() < 0.3:
        return _generate_random_primitive()
    
    container_type = random.choice(["list", "dict", "tuple", "set", "frozenset"])
    size = random.randint(0, 5)
    
    if container_type == "list":
        return [_generate_random_object(max_depth - 1) for _ in range(size)]
    
    if container_type == "dict":
        return {
            _generate_random_primitive_string(): _generate_random_object(max_depth - 1)
            for _ in range(size)
        }
    
    if container_type == "tuple":
        return tuple(_generate_random_object(max_depth - 1) for _ in range(size))
    
    if container_type == "set":
        return {_generate_random_primitive() for _ in range(size)}
    
    if container_type == "frozenset":
        return frozenset(_generate_random_primitive() for _ in range(size))
    
    return _generate_random_primitive()


def _generate_random_primitive() -> Any:
    """生成随机基本类型"""
    choice = random.choice([
        "none", "bool", "int", "float", "str", "bytes", "complex"
    ])
    
    if choice == "none":
        return None
    if choice == "bool":
        return random.choice([True, False])
    if choice == "int":
        return random.randint(-10**6, 10**6)
    if choice == "float":
        special = random.choice([None, "inf", "-inf", "nan"])
        if special == "inf":
            return float("inf")
        if special == "-inf":
            return float("-inf")
        if special == "nan":
            return float("nan")
        return random.uniform(-1e6, 1e6)
    if choice == "str":
        length = random.randint(0, 20)
        return ''.join(chr(random.randint(32, 126)) for _ in range(length))
    if choice == "bytes":
        length = random.randint(0, 20)
        return bytes(random.randint(0, 255) for _ in range(length))
    if choice == "complex":
        return complex(random.uniform(-100, 100), random.uniform(-100, 100))
    
    return None


def _generate_random_primitive_string() -> str:
    """生成随机字符串"""
    length = random.randint(1, 10)
    return ''.join(chr(random.randint(32, 126)) for _ in range(length))


# =====================================================
# 5. 白盒测试 - 基于 marshal.c 的路径覆盖
# =====================================================

def test_whitebox_coverage() -> Dict[str, Any]:
    """
    白盒测试 - 基于 marshal.c 实现的关键路径测试
    """
    print("\n" + "=" * 70)
    print("5. 白盒测试 - 基于 marshal.c 的路径覆盖")
    print("=" * 70)
    
    test_cases = _get_whitebox_test_cases()
    results = {
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test_name, obj, expected_behavior in test_cases:
        print(f"\n测试: {test_name}")
        
        try:
            data = marshal.dumps(obj)
            restored = marshal.loads(data)
            
            if _safe_compare(obj, restored):
                results["passed"] += 1
                print(f"  ✓ 通过: {len(data)} 字节")
            else:
                results["failed"] += 1
                print(f"  ✗ 失败: 值不匹配")
                
        except Exception as e:
            if expected_behavior == "should_fail":
                results["passed"] += 1
                print(f"  ✓ 通过: 预期失败 - {e}")
            else:
                results["failed"] += 1
                print(f"  ✗ 失败: 未预期的错误 - {e}")
    
    print(f"\n白盒测试结果: {results['passed']}/{len(test_cases)} 通过")
    return results


def _get_whitebox_test_cases() -> List[Tuple[str, Any, str]]:
    """获取白盒测试用例"""
    test_cases = []
    
    test_cases.append(("TypeNone", None, "should_succeed"))
    test_cases.append(("TypeBool_True", True, "should_succeed"))
    test_cases.append(("TypeBool_False", False, "should_succeed"))
    test_cases.append(("TypeInt_Small", 42, "should_succeed"))
    test_cases.append(("TypeInt_Large", 2**100, "should_succeed"))
    test_cases.append(("TypeFloat", 3.14159, "should_succeed"))
    test_cases.append(("TypeFloat_Inf", float("inf"), "should_succeed"))
    test_cases.append(("TypeFloat_NaN", float("nan"), "should_succeed"))
    test_cases.append(("TypeComplex", 1+2j, "should_succeed"))
    test_cases.append(("TypeString", "hello", "should_succeed"))
    test_cases.append(("TypeString_Long", "a" * 1000, "should_succeed"))
    
    s = "repeated_string"
    test_cases.append(("TypeStringRef", [s, s, s], "should_succeed"))
    test_cases.append(("TypeUnicode", "你好世界", "should_succeed"))
    test_cases.append(("TypeTuple", (1, 2, 3), "should_succeed"))
    test_cases.append(("TypeList", [1, 2, 3], "should_succeed"))
    test_cases.append(("TypeDict", {"a": 1, "b": 2}, "should_succeed"))
    test_cases.append(("TypeDict_IntKeys", {1: "a", 2: "b"}, "should_succeed"))
    test_cases.append(("TypeSet", {1, 2, 3}, "should_succeed"))
    test_cases.append(("TypeFrozenSet", frozenset([1, 2, 3]), "should_succeed"))
    
    # 自引用 - 预期成功
    self_ref = []
    self_ref.append(self_ref)
    test_cases.append(("TypeRef", self_ref, "should_succeed"))
    
    # 深层嵌套 - 预期失败（超过递归限制）
    deep = []
    current = deep
    for i in range(2000):
        current.append([])
        current = current[-1]
    test_cases.append(("DeepNested", deep, "should_fail"))
    
    return test_cases


# =====================================================
# 6. 完整测试套件
# =====================================================

class MarshalTestSuite:
    """完整的 Marshal 测试套件"""
    
    def __init__(self):
        self.results = {}
        self.start_time = None
        self.end_time = None
    
    def run_all_tests(self):
        """运行所有测试"""
        print("=" * 70)
        print("Marshal 模块完整测试套件")
        print(f"Python 版本: {sys.version}")
        print(f"操作系统: {platform.system()} {platform.release()}")
        print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70)
        
        self.start_time = time.time()
        
        self.results["determinism"] = test_determinism()
        self.results["recursive"] = test_recursive_structures()
        self.results["boundary"] = test_boundary_values()
        self.results["fuzzing"] = test_fuzzing()
        self.results["whitebox"] = test_whitebox_coverage()
        
        self.end_time = time.time()
        
        self._print_summary()
        self._save_results()
        
        return self.results
    
    def _print_summary(self):
        """打印测试总结"""
        print("\n" + "=" * 70)
        print("测试总结")
        print("=" * 70)
        
        total_passed = 0
        total_failed = 0
        
        for test_name, result in self.results.items():
            passed = result.get("passed", 0)
            failed = result.get("failed", 0)
            total_passed += passed
            total_failed += failed
            
            total = passed + failed
            status = "✓" if failed == 0 else "✗"
            print(f"{status} {test_name}: {passed}/{total} 通过")
        
        print("-" * 70)
        total_total = total_passed + total_failed
        if total_total > 0:
            print(f"总计: {total_passed}/{total_total} 通过 ({total_passed/total_total*100:.1f}%)")
        print(f"耗时: {self.end_time - self.start_time:.2f} 秒")
        print("=" * 70)
    
    def _save_results(self):
        """保存测试结果"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"marshal_test_results_{timestamp}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("Marshal 模块测试结果\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Python 版本: {sys.version}\n")
            f.write(f"操作系统: {platform.system()} {platform.release()}\n")
            f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            for test_name, result in self.results.items():
                f.write(f"\n{test_name.upper()}\n")
                f.write("-" * 40 + "\n")
                
                for detail in result.get("details", [])[:20]:
                    f.write(f"{detail}\n")
        
        print(f"\n详细结果已保存到: {filename}")


# =====================================================
# 主函数
# =====================================================

def main():
    suite = MarshalTestSuite()
    suite.run_all_tests()


if __name__ == "__main__":
    main()