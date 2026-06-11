"""
轻量化测试：只为 Ellipsis、StopIteration、slice、pyc 文件、code object 生成哈希值
"""

import sys
import marshal
import hashlib
import importlib.util
import hashlib as hash_lib

def main():
    print("=" * 70)
    print("轻量化测试 - 核心对象 Marshal 哈希值")
    print("=" * 70)
    print(f"Python 版本: {sys.version}")
    print(f"Marshal 版本: {marshal.version}")
    print("=" * 70)
    
    print("\nLIGHTWEIGHT_MARSHAL_HASHES = {")
    
    # 1. Ellipsis
    data = marshal.dumps(Ellipsis)
    hash_val = hashlib.md5(data).hexdigest()
    print(f'    "Ellipsis": "{hash_val}",')
    
    # 2. StopIteration
    data = marshal.dumps(StopIteration)
    hash_val = hashlib.md5(data).hexdigest()
    print(f'    "StopIteration": "{hash_val}",')
    
    # 3. slice (预期失败)
    try:
        data = marshal.dumps(slice(1, 10, 2))
        hash_val = hashlib.md5(data).hexdigest()
        print(f'    "slice": "{hash_val}",')
    except ValueError:
        print(f'    "slice": None,  # ValueError: unsupported type')
    
    # 4. code object
    code_obj = compile("print('hello')", "<test>", "exec")
    data = marshal.dumps(code_obj)
    hash_val = hashlib.md5(data).hexdigest()
    print(f'    "code_object": "{hash_val}",')
    
    # 5. pyc 文件结构 (时间戳模式)
    MAGIC = importlib.util.MAGIC_NUMBER
    BITFIELD = 0b00
    TIMESTAMP = 1234567890
    code_for_pyc = compile("print('hello')", "<pyc>", "exec")
    pyc_tuple = (MAGIC, BITFIELD, TIMESTAMP, None, code_for_pyc)
    data = marshal.dumps(pyc_tuple)
    hash_val = hashlib.md5(data).hexdigest()
    print(f'    "pyc_timestamp_mode": "{hash_val}",')
    
    # 6. pyc 文件结构 (哈希模式)
    source_hash = hash_lib.sha256(b"source code").digest()
    pyc_hash_tuple = (MAGIC, BITFIELD, 0, source_hash, code_for_pyc)
    data = marshal.dumps(pyc_hash_tuple)
    hash_val = hashlib.md5(data).hexdigest()
    print(f'    "pyc_hash_mode": "{hash_val}",')
    
    print("}")
    
    print("\n" + "=" * 70)
    print("完成")
    print("=" * 70)

if __name__ == "__main__":
    main()