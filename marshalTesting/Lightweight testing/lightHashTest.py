"""
轻量化测试验证：验证当前 Python 版本的 marshal 输出是否与基准哈希一致
"""

import sys
import marshal
import hashlib
import importlib.util
import hashlib as hash_lib

# 基准哈希值（从 lightHash.py 生成）
LIGHTWEIGHT_MARSHAL_HASHES = {
    "Ellipsis": "5058f1af8388633f609cadb75a75dc9d",
    "StopIteration": "5dbc98dcc983a70728bd082d1a47546e",
    "slice": None,  # ValueError: unsupported type
    "code_object": "309f42ade3273786112954859b57e08e",
    "pyc_timestamp_mode": "0ad41e07cb32236df2f23b28114e0e07",
    "pyc_hash_mode": "7f8b7d087c034aff523fa856e04b069b",
}

def get_current_hashes():
    """获取当前 Python 环境下的哈希值"""
    current_hashes = {}
    
    # 1. Ellipsis
    data = marshal.dumps(Ellipsis)
    current_hashes["Ellipsis"] = hashlib.md5(data).hexdigest()
    
    # 2. StopIteration
    data = marshal.dumps(StopIteration)
    current_hashes["StopIteration"] = hashlib.md5(data).hexdigest()
    
    # 3. slice
    try:
        data = marshal.dumps(slice(1, 10, 2))
        current_hashes["slice"] = hashlib.md5(data).hexdigest()
    except ValueError:
        current_hashes["slice"] = None
    
    # 4. code object
    code_obj = compile("print('hello')", "<test>", "exec")
    data = marshal.dumps(code_obj)
    current_hashes["code_object"] = hashlib.md5(data).hexdigest()
    
    # 5. pyc 文件结构 (时间戳模式)
    MAGIC = importlib.util.MAGIC_NUMBER
    BITFIELD = 0b00
    TIMESTAMP = 1234567890
    code_for_pyc = compile("print('hello')", "<pyc>", "exec")
    pyc_tuple = (MAGIC, BITFIELD, TIMESTAMP, None, code_for_pyc)
    data = marshal.dumps(pyc_tuple)
    current_hashes["pyc_timestamp_mode"] = hashlib.md5(data).hexdigest()
    
    # 6. pyc 文件结构 (哈希模式)
    source_hash = hash_lib.sha256(b"source code").digest()
    pyc_hash_tuple = (MAGIC, BITFIELD, 0, source_hash, code_for_pyc)
    data = marshal.dumps(pyc_hash_tuple)
    current_hashes["pyc_hash_mode"] = hashlib.md5(data).hexdigest()
    
    return current_hashes

def main():
    print("=" * 70)
    print("轻量化测试验证 - 检查 Marshal 输出一致性")
    print("=" * 70)
    print(f"Python 版本: {sys.version}")
    print(f"Marshal 版本: {marshal.version}")
    print("=" * 70)
    
    # 获取当前哈希值
    current_hashes = get_current_hashes()
    
    # 比较并收集不一致的测试用例
    inconsistent_tests = []
    
    print("\n验证结果:")
    print("-" * 70)
    
    for test_name, baseline_hash in LIGHTWEIGHT_MARSHAL_HASHES.items():
        current_hash = current_hashes.get(test_name)
        
        if baseline_hash is None and current_hash is None:
            # 两者都不可序列化，一致
            print(f"✓ {test_name}: 一致 (均不可序列化)")
        elif baseline_hash is None and current_hash is not None:
            # 基准不可序列化，但当前可序列化
            print(f"✗ {test_name}: 不一致 - 基准不可序列化，但当前版本可序列化")
            print(f"  当前哈希: {current_hash}")
            inconsistent_tests.append(test_name)
        elif baseline_hash is not None and current_hash is None:
            # 基准可序列化，但当前不可序列化
            print(f"✗ {test_name}: 不一致 - 基准可序列化，但当前版本不可序列化")
            print(f"  基准哈希: {baseline_hash}")
            inconsistent_tests.append(test_name)
        elif baseline_hash == current_hash:
            # 哈希一致
            print(f"✓ {test_name}: 一致 (哈希: {current_hash[:16]}...)")
        else:
            # 哈希不一致
            print(f"✗ {test_name}: 不一致 - Marshal 输出发生变化")
            print(f"  基准哈希: {baseline_hash}")
            print(f"  当前哈希: {current_hash}")
            inconsistent_tests.append(test_name)
    
    # 输出总结
    print("\n" + "=" * 70)
    print("验证总结")
    print("=" * 70)
    
    total_tests = len(LIGHTWEIGHT_MARSHAL_HASHES)
    passed_tests = total_tests - len(inconsistent_tests)
    
    print(f"总测试用例: {total_tests}")
    print(f"通过: {passed_tests}")
    print(f"失败: {len(inconsistent_tests)}")
    print(f"通过率: {passed_tests/total_tests*100:.1f}%")
    
    if inconsistent_tests:
        print(f"\n不一致的测试用例: {', '.join(inconsistent_tests)}")
        
        # 生成当前环境的哈希表
        print("\n" + "=" * 70)
        print("当前环境的哈希表 (可用于更新基准)")
        print("=" * 70)
        print("\nLIGHTWEIGHT_MARSHAL_HASHES = {")
        for test_name, current_hash in current_hashes.items():
            if current_hash is None:
                print(f'    "{test_name}": None,')
            else:
                print(f'    "{test_name}": "{current_hash}",')
        print("}")
    else:
        print("\n✓ 所有测试用例均通过验证！Marshal 行为与基准一致。")
    
    print("\n" + "=" * 70)
    print("验证完成")
    print("=" * 70)

if __name__ == "__main__":
    main()