import json
import requests

# Загружаем тесты
with open('examples/test_payloads.json', 'r', encoding='utf-8') as f:
    test_data = json.load(f)

BASE_URL = "http://127.0.0.1:8000"

print("=" * 60)
print("🧪 ЗАПУСК ТЕСТОВ LEADCATCHER API")
print("=" * 60)

passed = 0
failed = 0

for test in test_data['tests']:
    print(f"\n[Test {test['id']}] {test['name']}")
    print(f"  Описание: {test['description']}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/lead",
            json=test['payload'],
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == test['expected_status']:
            print(f"  ✅ PASS (статус: {response.status_code})")
            passed += 1
        else:
            print(f"  ❌ FAIL (ожидался {test['expected_status']}, получено {response.status_code})")
            failed += 1
            
    except Exception as e:
        print(f"  ❌ ERROR: {e}")
        failed += 1

print("\n" + "=" * 60)
print(f"📊 РЕЗУЛЬТАТЫ: {passed} прошло, {failed} провалено")
print("=" * 60)