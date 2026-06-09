"""
将 marshal_cross.py 中的所有测试用例转化为哈希值
（经过 marshal.dumps() 再 marshal.loads() 复原后计算哈希）
并详细输出不一致的用例
"""

import sys
import marshal
import hashlib
import math
import random
from typing import Any, Dict, List, Tuple

# =====================================================
# 从 marshal_cross.py 复制的测试用例生成函数
# =====================================================

MAX_RECURSION_DEPTH = 100

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
    
    # 深层递归列表（限制深度避免过深）
    depth = min(MAX_RECURSION_DEPTH, 50)
    deep = []
    current = deep
    for i in range(depth):
        current.append([])
        current = current[-1]
    test_cases.append((f"DeepRecursion_{depth}", deep))
    
    return test_cases


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


def _get_whitebox_test_cases() -> List[Tuple[str, Any]]:
    """获取白盒测试用例"""
    test_cases = [
        ("TypeNone", None),
        ("TypeBool_True", True),
        ("TypeBool_False", False),
        ("TypeInt_Small", 42),
        ("TypeInt_Large", 2**100),
        ("TypeFloat", 3.14159),
        ("TypeFloat_Inf", float("inf")),
        ("TypeFloat_NaN", float("nan")),
        ("TypeComplex", 1+2j),
        ("TypeString", "hello"),
        ("TypeString_Long", "a" * 1000),
        ("TypeUnicode", "你好世界"),
        ("TypeTuple", (1, 2, 3)),
        ("TypeList", [1, 2, 3]),
        ("TypeDict", {"a": 1, "b": 2}),
        ("TypeDict_IntKeys", {1: "a", 2: "b"}),
        ("TypeSet", {1, 2, 3}),
        ("TypeFrozenSet", frozenset([1, 2, 3])),
    ]
    
    # 自引用
    self_ref = []
    self_ref.append(self_ref)
    test_cases.append(("TypeRef", self_ref))
    
    return test_cases


def _get_fuzzing_test_cases(fuzz_count=100, seed=42) -> List[Tuple[str, Any]]:
    """生成模糊测试用例"""
    random.seed(seed)
    test_cases = []
    
    for i in range(fuzz_count):
        obj = _generate_random_object(max_depth=3)
        test_cases.append((f"Fuzz_{i+1}", obj))
    
    return test_cases


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


def safe_marshal_roundtrip(obj: Any) -> Any:
    """
    安全的 marshal 往返：dumps -> loads
    返回反序列化后的对象
    """
    old_limit = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(10000)
        data = marshal.dumps(obj)
        restored = marshal.loads(data)
        return restored
    finally:
        sys.setrecursionlimit(old_limit)


def deep_compare(a, b, depth=0, path=""):
    """
    深度比较两个对象，返回是否相等以及详细的差异信息
    """
    if depth > 500:
        return True, ""
    
    if type(a) != type(b):
        return False, f"类型不匹配: {type(a).__name__} vs {type(b).__name__}"
    
    # 处理浮点数的特殊情况
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return True, ""
        if math.isinf(a) and math.isinf(b):
            if math.copysign(1, a) == math.copysign(1, b):
                return True, ""
            else:
                return False, f"符号不匹配: {a} vs {b}"
    
    if isinstance(a, (list, tuple)):
        if len(a) != len(b):
            return False, f"长度不匹配: {len(a)} vs {len(b)}"
        for i in range(len(a)):
            equal, msg = deep_compare(a[i], b[i], depth + 1, f"{path}[{i}]")
            if not equal:
                return False, msg
        return True, ""
    
    if isinstance(a, dict):
        if set(a.keys()) != set(b.keys()):
            keys_a = set(a.keys())
            keys_b = set(b.keys())
            only_a = keys_a - keys_b
            only_b = keys_b - keys_a
            return False, f"键不匹配 - 仅在原对象: {only_a}, 仅在复原对象: {only_b}"
        for k in a:
            equal, msg = deep_compare(a[k], b[k], depth + 1, f"{path}[{repr(k)}]")
            if not equal:
                return False, msg
        return True, ""
    
    if isinstance(a, (set, frozenset)):
        if len(a) != len(b):
            return False, f"集合大小不匹配: {len(a)} vs {len(b)}"
        # 对于集合，简化比较
        try:
            if a == b:
                return True, ""
            else:
                diff_a = a - b
                diff_b = b - a
                return False, f"集合元素差异 - 原对象多余: {diff_a}, 复原对象多余: {diff_b}"
        except:
            return False, "集合无法比较"
    
    # 普通值比较
    try:
        if a == b:
            return True, ""
        else:
            return False, f"值不匹配: {repr(a)} vs {repr(b)}"
    except:
        return False, f"无法比较: {repr(a)} vs {repr(b)}"


def hash_object(obj: Any) -> str:
    """
    计算对象经过 marshal 往返后的哈希值
    """
    def normalize_for_hash(o):
        """将对象标准化以便计算哈希"""
        if isinstance(o, float) and math.isnan(o):
            return "NaN"
        if isinstance(o, float) and math.isinf(o):
            return f"Inf_{math.copysign(1, o)}"
        if isinstance(o, complex):
            if math.isnan(o.real) or math.isnan(o.imag):
                return f"complex({normalize_for_hash(o.real)}, {normalize_for_hash(o.imag)})"
        if isinstance(o, (list, tuple)):
            return tuple(normalize_for_hash(x) for x in o)
        if isinstance(o, dict):
            return tuple(sorted((normalize_for_hash(k), normalize_for_hash(v)) for k, v in o.items()))
        if isinstance(o, (set, frozenset)):
            return frozenset(normalize_for_hash(x) for x in o)
        return o
    
    try:
        normalized = normalize_for_hash(obj)
        return hashlib.sha256(repr(normalized).encode()).hexdigest()
    except:
        try:
            data = marshal.dumps(obj)
            return hashlib.sha256(data).hexdigest()
        except:
            return None


def compute_roundtrip_hashes(test_cases: List[Tuple[str, Any]], verbose: bool = True) -> Dict[str, str]:
    """
    计算所有测试用例经过 marshal 往返后的哈希值
    """
    hashes = {}
    
    for name, obj in test_cases:
        try:
            restored = safe_marshal_roundtrip(obj)
            h = hash_object(restored)
            
            if h is not None:
                hashes[name] = h
                if verbose:
                    print(f'    "{name}": "{h}",')
            else:
                hashes[name] = None
                if verbose:
                    print(f'    "{name}": None,  # 无法计算哈希')
                    
        except Exception as e:
            hashes[name] = None
            if verbose:
                print(f'    "{name}": None,  # 错误: {type(e).__name__}: {e}')
    
    return hashes


def compare_original_and_roundtrip(test_cases: List[Tuple[str, Any]], verbose: bool = False) -> Dict[str, Tuple[bool, str]]:
    """
    比较原始对象和往返后的对象是否相等
    返回: {name: (is_equal, error_message)}
    """
    results = {}
    
    for name, obj in test_cases:
        try:
            restored = safe_marshal_roundtrip(obj)
            is_equal, msg = deep_compare(obj, restored)
            results[name] = (is_equal, msg)
            
            if verbose and not is_equal:
                print(f"\n  ✗ {name}: 不相等")
                print(f"     原因: {msg}")
        except Exception as e:
            results[name] = (False, f"异常: {type(e).__name__}: {e}")
            if verbose:
                print(f"\n  ✗ {name}: 错误 - {e}")
    
    return results


def main():
    print("=" * 70)
    print("marshal_cross.py 测试用例哈希值采集")
    print("（对象 -> marshal.dumps() -> marshal.loads() -> 计算哈希）")
    print(f"Python 版本: {sys.version}")
    print("=" * 70)
    
    # 收集所有测试用例
    all_test_cases = []
    
    print("\n# =====================================================")
    print("# 1. 确定性测试用例")
    print("# =====================================================")
    determinism_cases = _get_determinism_test_cases()
    all_test_cases.extend(determinism_cases)
    print(f"  已加载 {len(determinism_cases)} 个测试用例")
    
    print("\n# =====================================================")
    print("# 2. 递归/循环引用测试用例")
    print("# =====================================================")
    recursive_cases = _get_recursive_test_cases()
    all_test_cases.extend(recursive_cases)
    print(f"  已加载 {len(recursive_cases)} 个测试用例")
    
    print("\n# =====================================================")
    print("# 3. 边界值测试用例")
    print("# =====================================================")
    boundary_cases = _get_boundary_test_cases()
    all_test_cases.extend(boundary_cases)
    print(f"  已加载 {len(boundary_cases)} 个测试用例")
    
    print("\n# =====================================================")
    print("# 4. 白盒测试用例")
    print("# =====================================================")
    whitebox_cases = _get_whitebox_test_cases()
    all_test_cases.extend(whitebox_cases)
    print(f"  已加载 {len(whitebox_cases)} 个测试用例")
    
    print("\n# =====================================================")
    print("# 5. 模糊测试用例 (100个)")
    print("# =====================================================")
    fuzz_cases = _get_fuzzing_test_cases(fuzz_count=100, seed=42)
    all_test_cases.extend(fuzz_cases)
    print(f"  已加载 {len(fuzz_cases)} 个测试用例")
    
    print(f"\n总计: {len(all_test_cases)} 个测试用例")
    
    # 详细比较原始和往返后的对象是否相等
    print("\n" + "=" * 70)
    print("详细比较原始对象和往返后对象的一致性")
    print("=" * 70)
    
    comparison = compare_original_and_roundtrip(all_test_cases, verbose=True)
    
    equal_count = sum(1 for v in comparison.values() if v[0])
    total_count = len(comparison)
    
    print("\n" + "-" * 70)
    print(f"一致性统计: {equal_count}/{total_count} ({equal_count/total_count*100:.1f}%)")
    print("-" * 70)
    
    # 打印所有不相等用例的详细列表
    failed_tests = [(name, msg) for name, (is_equal, msg) in comparison.items() if not is_equal]
    
    if failed_tests:
        print("\n" + "=" * 70)
        print(f"不相等用例详细列表 (共 {len(failed_tests)} 个)")
        print("=" * 70)
        
        for i, (name, msg) in enumerate(failed_tests, 1):
            print(f"\n{i}. {name}")
            print(f"   原因: {msg}")
            
            # 获取原始对象和复原对象以便调试
            original_obj = next(obj for n, obj in all_test_cases if n == name)
            try:
                restored_obj = safe_marshal_roundtrip(original_obj)
                print(f"   原始对象: {repr(original_obj)[:200]}")
                print(f"   复原对象: {repr(restored_obj)[:200]}")
            except:
                pass
    else:
        print("\n✓ 所有测试用例都一致！")
    
    # 计算往返后的哈希
    print("\n" + "=" * 70)
    print("往返后对象的哈希值:")
    print("=" * 70)
    print()
    print("MARSHAL_ROUNDTRIP_BASELINE_HASHES = {")
    hashes = compute_roundtrip_hashes(all_test_cases, verbose=True)
    print("}")
    
    # 输出统计信息
    print("\n" + "=" * 70)
    print("统计信息:")
    print("=" * 70)
    total = len(hashes)
    success = sum(1 for h in hashes.values() if h is not None)
    failed = total - success
    print(f"总测试用例: {total}")
    print(f"成功计算哈希: {success}")
    print(f"失败计算哈希: {failed}")
    print(f"原始 == 往返后: {equal_count}/{total_count}")
    print("=" * 70)
    
    # 保存到文件
    import json
    from datetime import datetime
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"marshal_roundtrip_baseline_{timestamp}.json"
    
    output_data = {
        "python_version": sys.version,
        "timestamp": timestamp,
        "description": "Object -> marshal.dumps() -> marshal.loads() -> hash",
        "total_test_cases": total,
        "success_count": success,
        "failed_count": failed,
        "consistency_count": equal_count,
        "consistency_total": total_count,
        "inconsistent_tests": [
            {"name": name, "reason": msg} 
            for name, (is_equal, msg) in comparison.items() 
            if not is_equal
        ],
        "hashes": {k: v for k, v in hashes.items() if v is not None}
    }
    
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n详细结果已保存到: {filename}")
    
    # 如果有不一致的用例，也保存到单独的文本文件
    if failed_tests:
        detail_filename = f"inconsistent_tests_{timestamp}.txt"
        with open(detail_filename, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"不一致测试用例详情\n")
            f.write(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python: {sys.version}\n")
            f.write("=" * 70 + "\n\n")
            
            for i, (name, msg) in enumerate(failed_tests, 1):
                f.write(f"{i}. {name}\n")
                f.write(f"   原因: {msg}\n")
                
                original_obj = next(obj for n, obj in all_test_cases if n == name)
                try:
                    restored_obj = safe_marshal_roundtrip(original_obj)
                    f.write(f"   原始对象: {repr(original_obj)[:500]}\n")
                    f.write(f"   复原对象: {repr(restored_obj)[:500]}\n")
                except Exception as e:
                    f.write(f"   获取对象失败: {e}\n")
                f.write("\n")
        
        print(f"不一致用例详情已保存到: {detail_filename}")


if __name__ == "__main__":
    main()