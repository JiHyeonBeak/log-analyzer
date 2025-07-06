#!/usr/bin/env python3
"""
테스트 러너

이 스크립트는 모든 테스트를 실행하고 결과를 보고합니다.
"""

import unittest
import sys
import os
import time

# 프로젝트 루트를 Python 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


def run_all_tests():
    """모든 테스트를 실행합니다."""
    print("🧪 Magpie 로그 분석기 테스트 시작")
    print("=" * 50)
    
    # 테스트 디스커버리
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern='test_*.py')
    
    # 테스트 실행
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 결과 출력
    print("\n" + "=" * 50)
    print("📊 테스트 결과 요약")
    print("=" * 50)
    print(f"실행 시간: {end_time - start_time:.2f}초")
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ 실패한 테스트:")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print("\n🚨 오류가 발생한 테스트:")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    if result.wasSuccessful():
        print("\n✅ 모든 테스트가 성공했습니다!")
        return 0
    else:
        print("\n❌ 일부 테스트가 실패했습니다.")
        return 1


def run_specific_test(test_name):
    """특정 테스트를 실행합니다."""
    print(f"🧪 {test_name} 테스트 실행")
    print("=" * 50)
    
    # 테스트 모듈 임포트
    test_module = __import__(f'tests.{test_name}', fromlist=[''])
    
    # 테스트 실행
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(test_module)
    
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # 결과 출력
    print("\n" + "=" * 50)
    print(f"📊 {test_name} 테스트 결과")
    print("=" * 50)
    print(f"실행 시간: {end_time - start_time:.2f}초")
    print(f"실행된 테스트: {result.testsRun}")
    print(f"성공: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"실패: {len(result.failures)}")
    print(f"오류: {len(result.errors)}")
    
    if result.wasSuccessful():
        print(f"\n✅ {test_name} 테스트가 성공했습니다!")
        return 0
    else:
        print(f"\n❌ {test_name} 테스트가 실패했습니다.")
        return 1


def main():
    """메인 함수"""
    if len(sys.argv) > 1:
        # 특정 테스트 실행
        test_name = sys.argv[1]
        if test_name in ['test_utils', 'test_views', 'test_integration']:
            return run_specific_test(test_name)
        else:
            print(f"❌ 알 수 없는 테스트: {test_name}")
            print("사용 가능한 테스트: test_utils, test_views, test_integration")
            return 1
    else:
        # 모든 테스트 실행
        return run_all_tests()


if __name__ == '__main__':
    sys.exit(main()) 