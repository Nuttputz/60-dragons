def calculate_kua(year_of_birth_ad, gender):
    """
    ฟังก์ชันคำนวณรหัสบุคคล (Kua Number) และจัดกลุ่มราศีทิศมงคล
    year_of_birth_ad: ปีเกิด ค.ศ.
    gender: 'male' (ชาย) หรือ 'female' (หญิง)
    """
    # 1. หาผลรวมของตัวเลขปีเกิดจนกว่าจะเหลือหลักเดียว
    digit_sum = sum(int(d) for d in str(year_of_birth_ad))
    while digit_sum > 9:
        digit_sum = sum(int(d) for d in str(digit_sum))
        
    # 2. คำนวณรหัส Kua ตามเพศและช่วงปีเกิด
    if gender.lower() == 'male':
        kua = 11 - digit_sum if year_of_birth_ad < 2000 else 9 - digit_sum
        while kua > 9: kua -= 9
        if kua == 5: kua = 2 # ผู้ชายรหัส 5 ปรับเป็น 2
    else:
        kua = 4 + digit_sum if year_of_birth_ad < 2000 else 6 + digit_sum
        while kua > 9: kua -= 9
        if kua == 5: kua = 8 # ผู้หญิงรหัส 5 ปรับเป็น 8
        
    # 3. จัดกลุ่มราศีและทิศ
    east_group = [1, 3, 4, 9]
    if kua in east_group:
        group = "ราศีตะวันออก"
        good_dirs = ["ทิศเหนือ", "ทิศใต้", "ทิศตะวันออก", "ทิศตะวันออกเฉียงใต้"]
        bad_dirs = ["ทิศตะวันตก", "ทิศตะวันตกเฉียงเหนือ", "ทิศตะวันตกเฉียงใต้", "ทิศตะวันออกเฉียงเหนือ"]
    else:
        group = "ราศีตะวันตก"
        good_dirs = ["ทิศตะวันตก", "ทิศตะวันตกเฉียงเหนือ", "ทิศตะวันตกเฉียงใต้", "ทิศตะวันออกเฉียงเหนือ"]
        bad_dirs = ["ทิศเหนือ", "ทิศใต้", "ทิศตะวันออก", "ทิศตะวันออกเฉียงใต้"]
        
    return {
        "kua_number": kua,
        "group": group,
        "auspicious_directions": good_dirs,
        "inauspicious_directions": bad_dirs
    }

# ทดสอบระบบด้วยข้อมูลตัวอย่าง (เกิดปี ค.ศ. 1986, เพศชาย)
if __name__ == "__main__":
    test_profile = calculate_kua(1986, 'male')
    print("ผลการคำนวณรหัสบุคคล:")
    print(f"รหัส Kua: {test_profile['kua_number']}")
    print(f"กลุ่ม: {test_profile['group']}")
    print(f"ทิศมงคล 4 ทิศ: {', '.join(test_profile['auspicious_directions'])}")
    print(f"ทิศอัปมงคล 4 ทิศ: {', '.join(test_profile['inauspicious_directions'])}")