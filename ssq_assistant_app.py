import os
import sys
import json
import time
import datetime
import webbrowser
import threading
from flask import Flask, render_template_string, jsonify, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = "ssq_engineering_assistant_secret_key_v6"

base_dir = os.path.dirname(os.path.abspath(__file__)) if '__file__' in globals() else '/workspace/scratch'
DATA_FILE = os.path.join(base_dir, "ssq_assistant_data.json")

DEFAULT_USERS = {
    "chief_engineer": {
        "username": "chief_engineer",
        "display_name": "Главный инженер",
        "title_badge": "👑 ГЛАВНЫЙ ИНЖЕНЕР",
        "password": "1111",
        "must_change": True
    },
    "chief_mechanic": {
        "username": "chief_mechanic",
        "display_name": "Главный механик",
        "title_badge": "🔧 ГЛАВНЫЙ МЕХАНИК",
        "password": "1111",
        "must_change": True
    },
    "electronics_engineer": {
        "username": "electronics_engineer",
        "display_name": "Инженер-электроник",
        "title_badge": "⚡ ИНЖЕНЕР-ЭЛЕКТРОНИК",
        "password": "1111",
        "must_change": True
    }
}

ROLE_LOCALIZATIONS = {
    "chief_engineer": {
        "ru": "👑 ГЛАВНЫЙ ИНЖЕНЕР",
        "kk": "👑 БАС ИНЖЕНЕР",
        "ko": "👑 수석 엔지니어",
        "en": "👑 CHIEF ENGINEER"
    },
    "chief_mechanic": {
        "ru": "🔧 ГЛАВНЫЙ МЕХАНИК",
        "kk": "🔧 БАС МЕХАНИК",
        "ko": "🔧 수석 정비사",
        "en": "🔧 CHIEF MECHANIC"
    },
    "electronics_engineer": {
        "ru": "⚡ ИНЖЕНЕР-ЭЛЕКТРОНИК",
        "kk": "⚡ ЭЛЕКТРОНИК ИНЖЕНЕР",
        "ko": "⚡ 전자 엔지니어",
        "en": "⚡ ELECTRONICS ENGINEER"
    }
}

KB_TRANSLATIONS = {
    "kb_fanuc": {
        "category": {
            "ru": "Автоматика / Робототехника",
            "kk": "Автоматика / Робототехника",
            "ko": "자동화 / 로봇 공학",
            "en": "Automation & Robotics"
        },
        "title": {
            "ru": "Роботы FANUC M-900iB/360: Инструкция и сброс ошибок",
            "kk": "FANUC M-900iB/360 роботтары: Нұсқаулық және қателерді жою",
            "ko": "FANUC M-900iB/360 로봇: 매뉴얼 및 알람 리셋",
            "en": "FANUC M-900iB/360 Robots: Manual and Alarm Reset"
        },
        "content": {
            "ru": "Сброс ошибки SRVO-062 (Pulse Alarm):\n1. На пульте Teach Pendant переключите ключ в режим T1.\n2. Выберите [MENU] -> [SYSTEM] -> [Master/Cal] (если нет пункта, задайте $MASTER_ENB = 1).\n3. Совместите физические риски Witness Marks для осей J1-J6.\n4. Выберите [3 RES_PULSE] -> нажмите F3 [YES].\n5. Поверните оси вручную на 15+ градусов.\n6. Выберите [1 ZERO POSITION MASTER] -> [6 CALIBRATE] -> нажмите RESET.",
            "kk": "SRVO-062 (Pulse Alarm) қатесін сброс жасау процедурасы:\n1. Teach Pendant пультiндегi кiлттi T1 режимiне ауыстырыңыз.\n2. [MENU] -> [SYSTEM] -> [Master/Cal] таңдаңыз (тармақ болмаса $MASTER_ENB = 1 орнатыңыз).\n3. J1-J6 остерi үшiн Witness Marks физикалық белгiлерiн сәйкестендiрiңiз.\n4. [3 RES_PULSE] таңдап -> F3 [YES] басыңыз.\n5. Остердi қолмен 15+ градусқа бұрыңыз.\n6. [1 ZERO POSITION MASTER] -> [6 CALIBRATE] таңдап -> RESET басыңыз.",
            "ko": "SRVO-062 (Pulse Alarm) 알람 리셋 절차:\n1. Teach Pendant 키 스위치를 T1 모드로 전환합니다.\n2. [MENU] -> [SYSTEM] -> [Master/Cal] 이동 (항목이 없으면 $MASTER_ENB = 1 설정).\n3. J1-J6 축의 Witness Marks (영점 표식)를 정밀하게 맞춥니다.\n4. [3 RES_PULSE] 선택 -> F3 [YES] 눌러 펄스 리셋.\n5. 각 축을 수동으로 15도 이상 회전시킵니다.\n6. [1 ZERO POSITION MASTER] -> [6 CALIBRATE] 선택 후 RESET 버튼을 누릅니다.",
            "en": "SRVO-062 (Pulse Alarm) Reset Procedure:\n1. Switch Teach Pendant key to T1 mode.\n2. Select [MENU] -> [SYSTEM] -> [Master/Cal] (if missing, set $MASTER_ENB = 1).\n3. Align physical Witness Marks for axes J1-J6.\n4. Select [3 RES_PULSE] -> press F3 [YES].\n5. Manually rotate axes by 15+ degrees.\n6. Select [1 ZERO POSITION MASTER] -> [6 CALIBRATE] -> press RESET."
        }
    },
    "kb_cicon": {
        "category": {
            "ru": "ПЛК и АСУ ТП",
            "kk": "ПЛК және БАҚ жүйелері",
            "ko": "PLC 및 제어 시스템",
            "en": "PLC & Control Systems"
        },
        "title": {
            "ru": "ПЛК CIMON CICON: Масштабирование токового сигнала 4-20 мА",
            "kk": "CIMON CICON ПЛК: 4-20 мА ток сигналын масштабтау",
            "ko": "CIMON CICON PLC: 4-20mA 전류 신호 스케일링",
            "en": "CIMON CICON PLC: 4-20mA Current Signal Scaling"
        },
        "content": {
            "ru": "Формула расчета в CICON Ladder: Bar = (mA - 4.0) / 16.0 * Max_Bar.\nПример для пресса 250 бар: при токе 12.0 мА давление = (12 - 4) / 16 * 250 = 125.0 бар.\nПри токе 13.6 мА давление = 150.0 бар.\nИспользуемые регистры: X/Y (дискретные входы/выходы), M (внутренние реле), K (энергонезависимые флаги), D (данные).",
            "kk": "CICON Ladder есептеу формуласы: Bar = (mA - 4.0) / 16.0 * Max_Bar.\n250 бар пресс мысалы: 12.0 мА токта қысым = (12 - 4) / 16 * 250 = 125.0 бар.\n13.6 мА токта қысым = 150.0 бар.\nҚолданылатын регистрлер: X/Y (дискретті кірістер/шығыстар), M (ішкі реле), K (энергияға тәуелсіз жалаушалар), D (деректер).",
            "ko": "CICON Ladder 연산 공식: Bar = (mA - 4.0) / 16.0 * Max_Bar.\n250 bar 프레스 예시: 12.0 mA 전류 시 압력 = (12 - 4) / 16 * 250 = 125.0 bar.\n13.6 mA 전류 시 압력 = 150.0 bar.\n사용 레지스터: X/Y (디지털 입출력), M (내부 릴레이), K (비휘발성 플래그), D (데이터 레지스터).",
            "en": "CICON Ladder calculation formula: Bar = (mA - 4.0) / 16.0 * Max_Bar.\nExample for 250 bar press: at 12.0 mA current pressure = (12 - 4) / 16 * 250 = 125.0 bar.\nAt 13.6 mA current pressure = 150.0 bar.\nUsed registers: X/Y (discrete I/O), M (internal relays), K (non-volatile flags), D (data registers)."
        }
    },
    "kb_loto": {
        "category": {
            "ru": "Охрана труда и ТБ",
            "kk": "Еңбекті қорғау және ТҚ",
            "ko": "산업 안전 및 LOTO",
            "en": "HSE & LOTO Protocols"
        },
        "title": {
            "ru": "Регламент безопасной блокировки источников энергии LOTO (ГОСТ РК)",
            "kk": "LOTO энергия көздерін қауіпсіз бұғаттау регламенті (ҚР МЕМСТ)",
            "ko": "LOTO 에너지원 안전 잠금 규정 (카자흐스탄 국가 표준)",
            "en": "LOTO Energy Lockout Procedure (Kazakhstan GOST)"
        },
        "content": {
            "ru": "Последовательность LOTO:\n1. Оповещение смены\n2. Безопасный останов (Shutdown)\n3. Отключение вводного автомата\n4. Сброс остаточного давления гидравлики/пневматики до 0 бар\n5. Установка индивидуального замка и бирки\n6. Проверка нулевого энергетического состояния\n7. Выполнение работ\n8. Снятие блокировки.",
            "kk": "LOTO қауіпсіздік бұғаттау реті:\n1. Ауысымды хабарландыру\n2. Қауіпсіз тоқтату (Shutdown)\n3. Кіріс автоматын өшіру\n4. Гидравлика/пневматика қалдық қысымын 0 барға дейін түсіру\n5. Жеке құлып пен бирканы орнату\n6. Нөлдік энергетикалық күйді тексеру\n7. Жұмыстарды орындау\n8. Бұғаттауды шешу.",
            "ko": "LOTO 안전 차단 절차:\n1. 작업 조 알림\n2. 안전 정지 (Shutdown)\n3. 메인 전원 차단기 차단\n4. 유압/공압 잔류 압력 0 bar로 방출\n5. 개인 잠금장치(Padlock) 및 태그(Tag) 부착\n6. 제로 에너지 상태 검증\n7. 정비 작업 수행\n8. 잠금 해제 및 가동.",
            "en": "LOTO Safety Lockout Sequence:\n1. Shift notification\n2. Safe shutdown\n3. Main circuit breaker trip\n4. Release residual hydraulic/pneumatic pressure to 0 bar\n5. Apply personal lockout padlock and tagout tag\n6. Verify zero energy state\n7. Execute maintenance work\n8. Remove lockout and restore power."
        }
    },
    "kb_torque": {
        "category": {
            "ru": "КИПиА и Инструмент",
            "kk": "ӨҚА және Құрал-саймандар",
            "ko": "계측 및 공구",
            "en": "Instrumentation & Tools"
        },
        "title": {
            "ru": "Поверка и калибровка пневмогайковертов",
            "kk": "Пневматикалық гайка бұрауыштарды тексеру және калибрлеу",
            "ko": "에어 임팩트 렌치 점검 및 교정",
            "en": "Pneumatic Impact Wrench Calibration and Testing"
        },
        "content": {
            "ru": "Условия поверки: Давление воздуха 5.5 кгс/см² (бар).\nВыполняется 3 контрольных замера моментомером. Вычисляется среднее значение M_ср.\nЕсли отклонение от нормы (45.0 Н·м) превышает допуск, производится подстройка пружины клапана микроотверткой с фиксацией в журнале.",
            "kk": "Тексеру шарттары: Ауа қысымы 5.5 кгс/см² (бар).\nМоментомермен 3 бақылау өлшеуі орындалады. Орташа M_орт мәні есептеледі.\nНормадан (45.0 Н·м) ауытқу рұқсат етілген шектен асса, арнайы бұрауышпен клапан серіппесі реттеліп, журналға тіркеледі.",
            "ko": "점검 조건: 공기 압력 5.5 kgf/cm² (bar).\n토크 측정기로 3회 측정 실시 후 평균값 M_avg 계산.\n표준값(45.0 N·m) 오차가 허용 범위를 초과할 경우 마이크로 드라이버로 밸브 스프링 조정 후 일지에 기록.",
            "en": "Calibration conditions: Air pressure 5.5 kgf/cm² (bar).\nPerform 3 control measurements with torque meter. Calculate average value M_avg.\nIf deviation from standard (45.0 N·m) exceeds tolerance, adjust valve spring using micro-screwdriver and log in journal."
        }
    },
    "kb_equip_cat": {
        "category": {
            "ru": "ТОиР и Надежность",
            "kk": "ТЖҚ және Сенімділік",
            "ko": "유지보수 및 신뢰성",
            "en": "Maintenance & Reliability"
        },
        "title": {
            "ru": "Критерии категоризации оборудования (Категории A, B, C)",
            "kk": "Жабдықтарды санаттау критерийлері (A, B, C санаттары)",
            "ko": "설비 카테고리 분류 기준 (A, B, C 카테고리)",
            "en": "Equipment Categorization Criteria (Categories A, B, C)"
        },
        "content": {
            "ru": "Оценка проводится по 11 критериям (сложность, износ, влияние на качество и останов линии):\n• Категория A (>80 баллов, новое >32 б.): Критическое оборудование (останов завода). Регламент: Daily + TBM + CBM.\n• Категория B (51-79 баллов, новое 23-31 б.): Важное оборудование (снижение мощности). Регламент: Daily + TBM.\n• Категория C (<50 баллов, новое <22 б.): Вспомогательное оборудование. Регламент: Daily осмотр.",
            "kk": "Бағалау 11 критерий бойынша жүргізіледі (күрделілік, тозу, сапаға әсері және желінің тоқтау қаупі):\n• A санаты (>80 балл, жаңа >32 б.): Критикалық жабдық (зауыттың тоқтауы). Регламент: Daily + TBM + CBM.\n• B санаты (51-79 балл, жаңа 23-31 б.): Маңызды жабдық (қуаттың төмендеуі). Регламент: Daily + TBM.\n• C санаты (<50 балл, жаңа <22 б.): Қосалқы жабдық. Регламент: Daily тексеру.",
            "ko": "11개 항목에 따른 등급 평가 실시 (복잡성, 마모도, 품질 영향 및 라인 중단 위험):\n• A 등급 (>80점, 신규 >32점): 치명적 장비 (공장 전면 중단). 관리 규정: Daily + TBM + CBM.\n• B 등급 (51-79점, 신규 23-31점): 중요 장비 (생산 능력 저하). 관리 규정: Daily + TBM.\n• C 등급 (<50점, 신규 <22점): 보조 장비. 관리 규정: Daily 점검.",
            "en": "Assessment conducted across 11 criteria (complexity, wear, quality impact, and line stoppage risk):\n• Category A (>80 pts, new >32 pts): Critical equipment (plant shutdown). Protocol: Daily + TBM + CBM.\n• Category B (51-79 pts, new 23-31 pts): Important equipment (power/capacity reduction). Protocol: Daily + TBM.\n• Category C (<50 pts, new <22 pts): Auxiliary equipment. Protocol: Daily inspection."
        }
    },
    "kb_voc_utility": {
        "category": {
            "ru": "Экология и Инженерные сети",
            "kk": "Экология және Инженерлік желілер",
            "ko": "환경 및 유틸리티",
            "en": "Utilities & Ecology"
        },
        "title": {
            "ru": "Компрессорная станция, градирни 150RT и башня VOC",
            "kk": "Компрессорлық станция, 150RT салқындату мұнарасы және VOC бағаны",
            "ko": "컴프레서 하우스, 150RT 냉각탑 및 VOC 흡착탑",
            "en": "Compressor House, 150RT Cooling Towers & VOC Tower"
        },
        "content": {
            "ru": "MAIN AIR: Винтовые компрессоры Atlas Copco (давление 5.5-6.0 бар).\nОхлаждение: Градирни Cooling Tower 150RT/200RT (расход 2300-3400 л/мин), бак SUS Water Tank 20т.\nЭкология: Адсорбционная башня VOC с 2.5т активированного угля (эффективность 96.5%). Обрези отходов PU и прочих материалов передаются лицензированным организациям.",
            "kk": "MAIN AIR: Atlas Copco бұрандалы компрессорлары (қысым 5.5-6.0 бар).\nСалқындату: Cooling Tower 150RT/200RT салқындату мұнаралары (шығын 2300-3400 л/мин), SUS Water Tank 20т багы.\nЭкология: 2.5т белсендірілген көмірмен VOC адсорбциялық мұнарасы (тиімділігі 96.5%). PU қалдықтары лицензияланған ұйымдарға тапсырылады.",
            "ko": "MAIN AIR: Atlas Copco 스크류 압축기 (압력 5.5-6.0 bar).\n냉각 시스템: Cooling Tower 150RT/200RT 쿨링 타워 (유량 2300-3400 L/min), SUS Water Tank 20t 탱크.\n환경 설비: 2.5t 활성탄 적용 VOC 흡착 타워 (흡착 효율 96.5%). 스크랩 및 폐기물은 전문 허가 업체에 위탁 처리.",
            "en": "MAIN AIR: Atlas Copco screw compressors (pressure 5.5-6.0 bar).\nCooling: Cooling Tower 150RT/200RT (flow 2300-3400 L/min), SUS Water Tank 20t.\nEcology: VOC Adsorption Tower with 2.5t activated carbon (efficiency 96.5%). PU waste scraps transferred to licensed disposal companies."
        }
    },
    "kb_roles": {
        "category": {
            "ru": "Должностные инструкции",
            "kk": "Лауазымдық нұсқаулықтар",
            "ko": "직무 명세서",
            "en": "Job Descriptions"
        },
        "title": {
            "ru": "Разграничение ответственности: Главный инженер, Механик, Электроник",
            "kk": "Жауапкершілікті бөлу: Бас инженер, Механик, Электроник",
            "ko": "책임 분담: 수석 엔지니어, 수석 정비사, 전자 엔지니어",
            "en": "Responsibility Allocation: Chief Engineer, Mechanic, Electronics"
        },
        "content": {
            "ru": "• Главный инженер: Общее техническое руководство, инженерные сети (градирни, VOC), стратегия ТОиР, экология и ТБ.\n• Главный механик: Механическая часть, гидравлика прессов 200Т/300Т, пневматика, конвейеры, смазочное хозяйство, графики ППР.\n• Инженер-электроник: Автоматика, ПЛК CIMON, панели HMI/XPBuilder, роботы FANUC, датчики, КИПиА, бэкапы ПО.",
            "kk": "• Бас инженер: Жалпы техникалық басшылық, инженерлік желілер (салқындату мұнаралары, VOC), ТЖҚ стратегиясы, экология және ЕҚ.\n• Бас механик: Механикалық бөлік, 200Т/300Т престердің гидравликасы, пневматика, конвейерлер, майлау шаруашылығы, ЖӨЖ кестелері.\n• Электроник инженер: Автоматика, CIMON ПЛК, HMI/XPBuilder панельдері, FANUC роботтары, датчиктер, ӨҚА, БҚ сақтық көшірмелері.",
            "ko": "• 수석 엔지니어: 총괄 기술 관리, 유틸리티 (쿨링타워, VOC), 유지보수 전략, 환경 및 산업 안전.\n• 수석 정비사: 기계 부품, 200T/300T 프레스 유압 시스템, 공압, 컨베이어, 윤활 관리, 예방 정비 일정.\n• 전자 엔지니어: 자동화, CIMON PLC, HMI/XPBuilder 터치패널, FANUC 로봇, 센서, 계측 제어, 소프트웨어 백업.",
            "en": "• Chief Engineer: General technical management, utility networks (cooling towers, VOC), maintenance strategy, ecology and HSE.\n• Chief Mechanic: Mechanical systems, 200T/300T press hydraulics, pneumatics, conveyors, lubrication, preventive maintenance schedules.\n• Electronics Engineer: Automation, CIMON PLC, HMI/XPBuilder touch panels, FANUC robots, sensors, instrumentation, software backups."
        }
    }
}

TEXT_TRANSLATIONS = {
    "Seat Foaming Line": {
        "ru": "Seat Foaming Line (Линия сидений)",
        "kk": "Seat Foaming Line (Орындықтар желісі)",
        "ko": "Seat Foaming Line (시트 라인)",
        "en": "Seat Foaming Line"
    },
    "H_Lin'g Line": {
        "ru": "H_Lin'g Line (Линия обивки потолка)",
        "kk": "H_Lin'g Line (Төбе қаптамасы желісі)",
        "ko": "H_Lin'g Line (헤드라이닝 라인)",
        "en": "H_Lin'g Line"
    },
    "Floor Carpet Line": {
        "ru": "Floor Carpet Line (Линия ковров)",
        "kk": "Floor Carpet Line (Кілемшелер желісі)",
        "ko": "Floor Carpet Line (카펫 라인)",
        "en": "Floor Carpet Line"
    },
    "Utility & Ecology": {
        "ru": "Utility & Ecology (Инженерные сети)",
        "kk": "Utility & Ecology (Инженерлік желілер)",
        "ko": "Utility & Ecology (유틸리티 및 환경)",
        "en": "Utility & Ecology"
    },
    "Критический": {"ru": "Критический", "kk": "Критикалық", "ko": "치명적", "en": "Critical"},
    "Critical": {"ru": "Критический", "kk": "Критикалық", "ko": "치명적", "en": "Critical"},
    "Высокий": {"ru": "Высокий", "kk": "Жоғары", "ko": "높음", "en": "High"},
    "High": {"ru": "Высокий", "kk": "Жоғары", "ko": "높음", "en": "High"},
    "Средний": {"ru": "Средний", "kk": "Орташа", "ko": "보통", "en": "Medium"},
    "Medium": {"ru": "Средний", "kk": "Орташа", "ko": "보통", "en": "Medium"},
    "Низкий": {"ru": "Низкий", "kk": "Төмен", "ko": "낮음", "en": "Low"},
    "Low": {"ru": "Низкий", "kk": "Төмен", "ko": "낮음", "en": "Low"},
    "Новая": {"ru": "Новая", "kk": "Жаңа", "ko": "신규", "en": "New"},
    "New": {"ru": "Новая", "kk": "Жаңа", "ko": "신규", "en": "New"},
    "В работе": {"ru": "В работе", "kk": "Орындалуда", "ko": "진행 중", "en": "In Progress"},
    "In Progress": {"ru": "В работе", "kk": "Орындалуда", "ko": "진행 중", "en": "In Progress"},
    "Выполнено": {"ru": "Выполнено", "kk": "Орындалды", "ko": "완료됨", "en": "Completed"},
    "Completed": {"ru": "Выполнено", "kk": "Орындалды", "ko": "완료됨", "en": "Completed"},
    "Дневная смена (08:00 - 17:00)": {
        "ru": "Дневная смена (08:00 - 17:00)",
        "kk": "Күндізгі ауысым (08:00 - 17:00)",
        "ko": "주간 근무 (08:00 - 17:00)",
        "en": "Day Shift (08:00 - 17:00)"
    },
    "Вечерняя смена (17:00 - 01:00)": {
        "ru": "Вечерняя смена (17:00 - 01:00)",
        "kk": "Кешкі ауысым (17:00 - 01:00)",
        "ko": "야간 근무 (17:00 - 01:00)",
        "en": "Evening Shift (17:00 - 01:00)"
    },
    "Ночная смена (01:00 - 08:00)": {
        "ru": "Ночная смена (01:00 - 08:00)",
        "kk": "Түнгі ауысым (01:00 - 08:00)",
        "ko": "심야 근무 (01:00 - 08:00)",
        "en": "Night Shift (01:00 - 08:00)"
    },
    "Проверка давления гидравлики Пресса 300Т": {
        "ru": "Проверка давления гидравлики Пресса 300Т",
        "kk": "300Т Пресс гидравликасының қысымын тексеру",
        "ko": "300T 프레스 유압 전압 점검",
        "en": "Inspection of 300T Press Hydraulic Pressure"
    },
    "Замер рабочего давления гидростанции (целевое: 210 бар) и инспекция уплотнений гидроцилиндров.": {
        "ru": "Замер рабочего давления гидростанции (целевое: 210 бар) и инспекция уплотнений гидроцилиндров.",
        "kk": "Гидростанцияның жұмыс қысымын өлшеу (нысаналы: 210 бар) және гидроцилиндр тығыздағыштарын тексеру.",
        "ko": "유압 유닛 작동 압력 측정 (목표: 210 bar) 및 실린더 씰 점검.",
        "en": "Measurement of hydraulic unit operating pressure (target: 210 bar) and cylinder seal inspection."
    },
    "Сброс ошибки FANUC SRVO-062 и Master/Cal": {
        "ru": "Сброс ошибки FANUC SRVO-062 и Master/Cal",
        "kk": "FANUC SRVO-062 қатесін сброс жасау және Master/Cal",
        "ko": "FANUC SRVO-062 알람 리셋 및 Master/Cal 영점 교정",
        "en": "Reset FANUC SRVO-062 error and Master/Cal"
    },
    "Сбросить ошибку Pulse Alarm на пульте Teach Pendant, проверить Witness Marks осей J1-J6.": {
        "ru": "Сбросить ошибку Pulse Alarm на пульте Teach Pendant, проверить Witness Marks осей J1-J6.",
        "kk": "Teach Pendant пультiнде Pulse Alarm қатесiн сброс жасап, J1-J6 остерiнiң Witness Marks белгiлерiн тексеру.",
        "ko": "Teach Pendant에서 Pulse Alarm 알람을 리셋하고 J1-J6 축의 Witness Marks 영점 표식을 확인하십시오.",
        "en": "Reset Pulse Alarm error on Teach Pendant and verify Witness Marks for J1-J6 axes."
    },
    "Ежемесячная поверка пневмогайковертов №101-105": {
        "ru": "Ежемесячная поверка пневмогайковертов №101-105",
        "kk": "№101-105 пневматикалық гайка бұрауыштарды айлық тексеру",
        "ko": "에어 임팩트 렌치 #101-105 월간 토크 정기 점검",
        "en": "Monthly calibration of pneumatic wrenches #101-105"
    },
    "3 замера момента при давлении воздуха 5.5 кгс/см². Корректировка спец-отверткой до 45.0 Н·м.": {
        "ru": "3 замера момента при давлении воздуха 5.5 кгс/см². Корректировка спец-отверткой до 45.0 Н·м.",
        "kk": "5.5 кгс/см² ауа қысымында 3 айналу моментін өлшеу. Арнайы бұрауышпен 45.0 Н·м дейін реттеу.",
        "ko": "공기 압력 5.5 kgf/cm²에서 3회 토크 측정. 마이크로 드라이버로 45.0 N·m까지 조정.",
        "en": "3 torque measurements at 5.5 kgf/cm² air pressure. Adjust with micro-screwdriver to 45.0 N·m."
    },
    "Замена угля в адсорбционной башне VOC (2.5 т)": {
        "ru": "Замена угля в адсорбционной башне VOC (2.5 т)",
        "kk": "VOC адсорбциялық мұнарасында көмірді ауыстыру (2.5 т)",
        "ko": "VOC 흡착탑 활성탄 교체 작업 (2.5t)",
        "en": "Replacement of activated carbon in VOC adsorption tower (2.5 t)"
    },
    "Регламентное обслуживание очистной башни VOC в рамках экологического сопровождения.": {
        "ru": "Регламентное обслуживание очистной башни VOC в рамках экологического сопровождения.",
        "kk": "Экологиялық сүйемелдеу шеңберінде VOC тазалау мұнарасына жоспарлы қызмет көрсету.",
        "ko": "환경 규성 준수를 위한 VOC 유해가스 흡착탑 정기 유지를 실시합니다.",
        "en": "Routine maintenance of VOC purification tower within ecological compliance guidelines."
    },
    "Проверка масштабирования 4-20 мА в CICON PLC": {
        "ru": "Проверка масштабирования 4-20 мА в CICON PLC",
        "kk": "CICON ПЛК-да 4-20 мА масштабтауды тексеру",
        "ko": "CICON PLC 4-20mA 아날로그 입력 스케일링 검증",
        "en": "Check 4-20 mA scaling in CICON PLC"
    },
    "Контроль шкалирования датчика давления печи в Ladder-программе ПЛК CIMON.": {
        "ru": "Контроль шкалирования датчика давления печи в Ladder-программе ПЛК CIMON.",
        "kk": "CIMON ПЛК Ladder бағдарламасында пештің қысым датчигінің масштабталуын бақылау.",
        "ko": "CIMON PLC Ladder 프로그램에서 오븐 압력 센서 스케일링 값을 확인하십시오.",
        "en": "Verify oven pressure sensor scaling in CIMON PLC Ladder logic program."
    },
    "Проведен утренний инструктаж ТБ. Проверены системы охлаждения 150RT и давление MAIN AIR (5.5 бар). Линии работают в штатном режиме.": {
        "ru": "Проведен утренний инструктаж ТБ. Проверены системы охлаждения 150RT и давление MAIN AIR (5.5 бар). Линии работают в штатном режиме.",
        "kk": "Таңертеңгі ЕҚ нұсқаулығы өткізілді. 150RT салқындату жүйелері мен MAIN AIR қысымы (5.5 бар) тексерілді. Желілер қалыпты режимде жұмыс істеп тұр.",
        "ko": "아침 산업 안전 교육 완료. 150RT 냉각 계통 및 MAIN AIR 압력(5.5 bar) 점검 완료. 전 라인 정상 가동 중.",
        "en": "Morning HSE briefing conducted. Checked 150RT cooling systems and MAIN AIR pressure (5.5 bar). Production lines operating normally."
    }
}

DEFAULT_DATA = {
    "users": DEFAULT_USERS,
    "tasks": [
        {
            "id": 1,
            "title": "Проверка давления гидравлики Пресса 300Т",
            "shop": "Floor Carpet Line",
            "assignee": "chief_mechanic",
            "created_by": "chief_engineer",
            "priority": "Высокий",
            "status": "В работе",
            "due": "2026-10-29",
            "desc": "Замер рабочего давления гидростанции (целевое: 210 бар) и инспекция уплотнений гидроцилиндров."
        },
        {
            "id": 2,
            "title": "Сброс ошибки FANUC SRVO-062 и Master/Cal",
            "shop": "Seat Foaming Line",
            "assignee": "electronics_engineer",
            "created_by": "chief_engineer",
            "priority": "Критический",
            "status": "Новая",
            "due": "2026-10-29",
            "desc": "Сбросить ошибку Pulse Alarm на пульте Teach Pendant, проверить Witness Marks осей J1-J6."
        },
        {
            "id": 3,
            "title": "Ежемесячная поверка пневмогайковертов №101-105",
            "shop": "Seat Foaming Line",
            "assignee": "chief_mechanic",
            "created_by": "chief_mechanic",
            "priority": "Средний",
            "status": "Выполнено",
            "due": "2026-10-28",
            "desc": "3 замера момента при давлении воздуха 5.5 кгс/см². Корректировка спец-отверткой до 45.0 Н·м."
        },
        {
            "id": 4,
            "title": "Замена угля в адсорбционной башне VOC (2.5 т)",
            "shop": "Utility & Ecology",
            "assignee": "chief_engineer",
            "created_by": "chief_engineer",
            "priority": "Средний",
            "status": "В работе",
            "due": "2026-11-02",
            "desc": "Регламентное обслуживание очистной башни VOC в рамках экологического сопровождения."
        },
        {
            "id": 5,
            "title": "Проверка масштабирования 4-20 мА в CICON PLC",
            "shop": "H_Lin'g Line",
            "assignee": "electronics_engineer",
            "created_by": "chief_engineer",
            "priority": "Низкий",
            "status": "Новая",
            "due": "2026-10-30",
            "desc": "Контроль шкалирования датчика давления печи в Ladder-программе ПЛК CIMON."
        }
    ],
    "planner_notes": [
        {
            "id": 1,
            "date": "2026-10-29",
            "shift": "Дневная смена (08:00 - 17:00)",
            "author": "chief_engineer",
            "loto_checked": True,
            "content": "Проведен утренний инструктаж ТБ. Проверены системы охлаждения 150RT и давление MAIN AIR (5.5 бар). Линии работают в штатном режиме."
        }
    ],
    "knowledge_base": [
        {
            "id": "kb_fanuc",
            "category": "Автоматика / Робототехника",
            "title": "Роботы FANUC M-900iB/360: Инструкция и сброс ошибок",
            "tags": "fanuc robot srvo-062 master cal pulse alarm t1 teach pendant",
            "author": "electronics_engineer",
            "content": "Сброс ошибки SRVO-062 (Pulse Alarm):\n1. На пульте Teach Pendant переключите ключ в режим T1.\n2. Выберите [MENU] -> [SYSTEM] -> [Master/Cal] (если нет пункта, задайте $MASTER_ENB = 1).\n3. Совместите физические риски Witness Marks для осей J1-J6.\n4. Выберите [3 RES_PULSE] -> нажмите F3 [YES].\n5. Поверните оси вручную на 15+ градусов.\n6. Выберите [1 ZERO POSITION MASTER] -> [6 CALIBRATE] -> нажмите RESET."
        },
        {
            "id": "kb_cicon",
            "category": "ПЛК и АСУ ТП",
            "title": "ПЛК CIMON CICON: Масштабирование токового сигнала 4-20 мА",
            "tags": "cimon cicon plc ladder 4-20ma аналоговый вход регистры d x y m k bar",
            "author": "electronics_engineer",
            "content": "Формула расчета в CICON Ladder: Bar = (mA - 4.0) / 16.0 * Max_Bar.\nПример для пресса 250 бар: при токе 12.0 мА давление = (12 - 4) / 16 * 250 = 125.0 бар.\nПри токе 13.6 мА давление = 150.0 бар.\nИспользуемые регистры: X/Y (дискретные входы/выходы), M (внутренние реле), K (энергонезависимые флаги), D (данные)."
        },
        {
            "id": "kb_loto",
            "category": "Охрана труда и ТБ",
            "title": "Регламент безопасной блокировки источников энергии LOTO (ГОСТ РК)",
            "tags": "loto безопасность тб блокировка электроэнергия гидравлика пневматика замок бирка",
            "author": "chief_engineer",
            "content": "Последовательность LOTO:\n1. Оповещение смены\n2. Безопасный останов (Shutdown)\n3. Отключение вводного автомата\n4. Сброс остаточного давления гидравлики/пневматики до 0 бар\n5. Установка индивидуального замка и бирки\n6. Проверка нулевого энергетического состояния\n7. Выполнение работ\n8. Снятие блокировки."
        },
        {
            "id": "kb_torque",
            "category": "КИПиА и Инструмент",
            "title": "Поверка и калибровка пневмогайковертов",
            "tags": "гайковерт момент поверка замер 45нм 5.5кгс давление микроотвертка",
            "author": "chief_mechanic",
            "content": "Условия поверки: Давление воздуха 5.5 кгс/см² (бар).\nВыполняется 3 контрольных замера моментомером. Вычисляется среднее значение M_ср.\nЕсли отклонение от нормы (45.0 Н·м) превышает допуск, производится подстройка пружины клапана микроотверткой с фиксацией в журнале."
        },
        {
            "id": "kb_equip_cat",
            "category": "ТОиР и Надежность",
            "title": "Критерии категоризации оборудования (Категории A, B, C)",
            "tags": "категория оборудования оценка баллы категории a b c tbm cbm mttr mtbf oee",
            "author": "chief_engineer",
            "content": "Оценка проводится по 11 критериям (сложность, износ, влияние на качество и останов линии):\n• Категория A (>80 баллов, новое >32 б.): Критическое оборудование (останов завода). Регламент: Daily + TBM + CBM.\n• Категория B (51-79 баллов, новое 23-31 б.): Важное оборудование (снижение мощности). Регламент: Daily + TBM.\n• Категория C (<50 баллов, новое <22 б.): Вспомогательное оборудование. Регламент: Daily осмотр."
        },
        {
            "id": "kb_voc_utility",
            "category": "Экология и Инженерные сети",
            "title": "Компрессорная станция, градирни 150RT и башня VOC",
            "tags": "voc уголь башня экология компрессор atlas copco main air 5.5бар градирня 150rt 200rt чиллер sus water tank",
            "author": "chief_engineer",
            "content": "MAIN AIR: Винтовые компрессоры Atlas Copco (давление 5.5-6.0 бар).\nОхлаждение: Градирни Cooling Tower 150RT/200RT (расход 2300-3400 л/мин), бак SUS Water Tank 20т.\nЭкология: Адсорбционная башня VOC с 2.5т активированного угля (эффективность 96.5%). Обрези отходов PU и прочих материалов передаются лицензированным организациям."
        },
        {
            "id": "kb_roles",
            "category": "Должностные инструкции",
            "title": "Разграничение ответственности: Главный инженер, Механик, Электроник",
            "tags": "главный инженер главный механик инженер электроник должностные обязанности полномочия",
            "author": "chief_engineer",
            "content": "• Главный инженер: Общее техническое руководство, инженерные сети (градирни, VOC), стратегия ТОиР, экология и ТБ.\n• Главный механик: Механическая часть, гидравлика прессов 200Т/300Т, пневматика, конвейеры, смазочное хозяйство, графики ППР.\n• Инженер-электроник: Автоматика, ПЛК CIMON, панели HMI/XPBuilder, роботы FANUC, датчики, КИПиА, бэкапы ПО."
        }
    ]
}

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "users" not in data or not data["users"]:
                    data["users"] = DEFAULT_USERS.copy()
                return data
        except Exception as e:
            print(f"Error loading data: {e}")
    return DEFAULT_DATA.copy()

def save_data(data):
    try:
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.flush()
            os.fsync(f.fileno())
    except Exception as e:
        print(f"Error saving data: {e}")

I18N = {
    "ru": {
        "title": "SEOYON SUMMIT QAZAQ — Инженерный Помогатор",
        "subtitle": "ИНЖЕНЕРНЫЙ ПОМОГАТОР И БАЗА ЗНАНИЙ (SSQ ASSISTANT v3.0)",
        "tab_dash": "📊 ГЛАВНАЯ ПАНЕЛЬ",
        "tab_planner": "📅 ЕЖЕДНЕВНИК И ЖУРНАЛ СМЕНЫ",
        "tab_tasks": "📋 РАБОЧИЕ ЗАДАЧИ И ТОИР",
        "tab_search": "🔍 БЫСТРЫЙ ПОИСК ПО БАЗЕ ЗНАНИЙ",
        "tab_calc": "🧮 СЕРВИСНЫЕ КАЛЬКУЛЯТОРЫ И КИПиА",
        "total_tasks": "Всего задач ТОиР",
        "in_progress": "В процессе выполнения",
        "critical_tasks": "Критическая заявка",
        "kb_articles": "Инструкций в базе знаний",
        "quick_actions": "🚀 БЫСТРЫЕ ДЕЙСТВИЯ И ЭКСПРЕСС-ШПАРГАЛКА",
        "active_tasks": "📌 ТЕКУЩИЕ АКТИВНЫЕ ЗАДАЧИ ТЕХНИЧЕСКОЙ СЛУЖБЫ",
        "line_status": "🏭 СТАТУС ЛИНИЙ И КАТЕГОРИИ",
        "roles_title": "👤 РАЗГРАНИЧЕНИЕ ПОЛНОМОЧИЙ И ЗОН ОТВЕТСТВЕННОСТИ",
        "add_task_btn": "+ СОЗДАТЬ НОВУЮ ЗАДАЧУ",
        "add_material_btn": "➕ ДОБАВИТЬ МАТЕРИАЛ В ПОМОГАТОР",
        "add_user_btn": "➕ Добавить учетную запись",
        "change_pass_btn": "🔑 Пароль",
        "logout_btn": "🚪 Выход",
        "login_title": "АВТОРИЗАЦИЯ В СИСТЕМЕ SSQ",
        "select_account": "Выберите вашу учетную запись:",
        "password_label": "Пароль доступа:",
        "login_submit": "ВОЙТИ В СИСТЕМУ",
        "change_pass_title": "СМЕНА СТАНДАРТНОГО ПАРОЛЯ",
        "change_pass_desc": "Вы вошли по первичному паролю. Пожалуйста, установите свой постоянный пароль для защиты аккаунта.",
        "new_pass_label": "Новый пароль:",
        "confirm_pass_label": "Подтвердите новый пароль:",
        "save_pass_btn": "СОХРАНИТЬ НОВЫЙ ПАРОЛЬ",
        "cancel_btn": "❌ Отмена (На главный экран)",
        "search_ph": "Введите ключевое слово (fanuc, cicon, loto, гайковерт, voc, категории)...",
        "author_label": "Автор:",
        "shop_label": "Цех / Линия:",
        "assignee_label": "Исполнитель:",
        "creator_label": "Создал:",
        "priority_label": "Приоритет:",
        "status_label": "Статус:",
        "view_instruction": "Открыть инструкцию",
        "more_info": "Подробнее",
        "reg_tb": "Регламент ТБ",
        "btn_save_planner": "СОХРАНИТЬ В ЖУРНАЛ СМЕНЫ",
        "btn_create_task": "СОХРАНИТЬ ЗАДАЧУ",
        "btn_create_kb": "СОХРАНИТЬ МАТЕРИАЛ В ПОМОГАТОР",
        "modal_task_title": "Создание новой задачи ТОиР",
        "modal_kb_title": "Добавление инструкции / материала в Помогатор",
        "modal_user_title": "Создание новой учетной записи",
        "lbl_kb_category": "Категория:",
        "ph_kb_category": "Например: Автоматика / Робототехника",
        "lbl_kb_title": "Заголовок статьи / инструкции:",
        "ph_kb_title": "Например: Регламент проверки насоса 150RT",
        "lbl_kb_tags": "Ключевые слова (теги):",
        "ph_kb_tags": "Например: насос градирня 150rt охлаждение",
        "lbl_kb_content": "Полный текст инструкции:",
        "ph_kb_content": "Введите подробные пошаговые указания...",
        "lbl_user_name": "ФИО / Должность:",
        "ph_user_name": "Например: Мастер смены Ануар",
        "lbl_user_role": "Титул с иконкой:",
        "ph_user_role": "Например: 👨‍🔧 МАСТЕР СМЕНЫ",
        "lbl_user_id": "Логин (ID):",
        "ph_user_id": "Например: shift_master",
        "btn_create_user": "СОХРАНИТЬ АККАУНТ"
    },
    "kk": {
        "title": "SEOYON SUMMIT QAZAQ — Инженерлік Көмекші",
        "subtitle": "ИНЖЕНЕРЛІК КӨМЕКШІ ЖӘНЕ БІЛІМ БАЗАСЫ (SSQ ASSISTANT v3.0)",
        "tab_dash": "📊 БАСТЫ ПАНЕЛЬ",
        "tab_planner": "📅 КҮННЕЛІК ЖӘНЕ АУЫСЫМ ЖУРНАЛЫ",
        "tab_tasks": "📋 ТЖҚ ЖӘНЕ ЖҰМЫС ТАПСЫРМАЛАРЫ",
        "tab_search": "🔍 БІЛІМ БАЗАСЫНДАН ЖЕДЕЛ ИЗДЕУ",
        "tab_calc": "🧮 СЕРВИСТІК КАЛЬКУЛЯТОРЛАР ЖӘНЕ ӨҚА",
        "total_tasks": "ТЖҚ тапсырмаларының саны",
        "in_progress": "Орындалу процесінде",
        "critical_tasks": "Критикалық өтінімдер",
        "kb_articles": "Білім базасындағы нұсқаулықтар",
        "quick_actions": "🚀 ЖЕДЕЛ ӘРЕКЕТТЕР ЖӘНЕ ЭКСПРЕСС-ШПАРГАЛКА",
        "active_tasks": "📌 ТЕХНИКАЛЫҚ ҚЫЗМЕТТІҢ БЕЛСЕНДІ ТАПСЫРМАЛАРЫ",
        "line_status": "🏭 ЖЕЛІЛЕР МӘРТЕБЕСІ ЖӘНЕ САНАТТАРЫ",
        "roles_title": "👤 ӨКІЛЕТТІКТЕРДІ ЖӘНЕ ЖАУАПКЕРШІЛІК АЙМАҚТАРЫН БӨЛУ",
        "add_task_btn": "+ ЖАҢА ТАПСЫРМА ЖАСАУ",
        "add_material_btn": "➕ КӨМЕКШІГЕ МАТЕРИАЛ ҚОСУ",
        "add_user_btn": "➕ Тіркелгі жазбасын қосу",
        "change_pass_btn": "🔑 Құпия сөз",
        "logout_btn": "🚪 Шығу",
        "login_title": "SSQ ЖҮЙЕСІНЕ КІРУ",
        "select_account": "Тіркелгі жазбаңызды таңдаңыз:",
        "password_label": "Кіру құпия сөзі:",
        "login_submit": "ЖҮЙЕГЕ КІРУ",
        "change_pass_title": "СТАНДАРТТЫ ҚҰПИЯ СӨЗДІ АУЫСТЫРУ",
        "change_pass_desc": "Сіз бастапқы құпия сөзбен кірдіңіз. Тіркелгіні қорғау үшін тұрақты құпия сөзіңізді орнатыңыз.",
        "new_pass_label": "Жаңа құпия сөз:",
        "confirm_pass_label": "Жаңа құпия сөзді растаңыз:",
        "save_pass_btn": "ЖАҢА ҚҰПИЯ СӨЗДІ САҚТАУ",
        "cancel_btn": "❌ Бас тарту (Басты экранға)",
        "search_ph": "Кілт сөзді енгізіңіз (fanuc, cicon, loto, гайковерт, voc)...",
        "author_label": "Авторы:",
        "shop_label": "Цех / Желі:",
        "assignee_label": "Орындаушы:",
        "creator_label": "Жасаған:",
        "priority_label": "Басымдылық:",
        "status_label": "Мәртебесі:",
        "view_instruction": "Нұсқаулықты ашу",
        "more_info": "Толығырақ",
        "reg_tb": "ҚТ Регламенті",
        "btn_save_planner": "АУЫСЫМ ЖУРНАЛЫНА САҚТАУ",
        "btn_create_task": "ТАПСЫРМАНЫ САҚТАУ",
        "btn_create_kb": "МАТЕРИАЛДЫ КӨМЕКШІГЕ САҚТАУ",
        "modal_task_title": "Жаңа ТЖҚ тапсырмасын жасау",
        "modal_kb_title": "Көмекшіге нұсқаулық / материал қосу",
        "modal_user_title": "Жаңа тіркелгі жазбасын жасау",
        "lbl_kb_category": "Санаты:",
        "ph_kb_category": "Мысалы: Автоматика / Робототехника",
        "lbl_kb_title": "Мақала / нұсқаулық тақырыбы:",
        "ph_kb_title": "Мысалы: 150RT сорғысын тексеру регламенті",
        "lbl_kb_tags": "Кілт сөздер (тегтер):",
        "ph_kb_tags": "Мысалы: сорғы градирня 150rt салқындату",
        "lbl_kb_content": "Нұсқаулықтың толық мәтіні:",
        "ph_kb_content": "Толық қадамдық нұсқауларды енгізіңіз...",
        "lbl_user_name": "АБЖ / Лауазымы:",
        "ph_user_name": "Мысалы: Ауысым шебері Ануар",
        "lbl_user_role": "Белгішесі бар лауазымы:",
        "ph_user_role": "Мысалы: 👨‍🔧 АУЫСЫМ ШЕБЕРІ",
        "lbl_user_id": "Логин (ID):",
        "ph_user_id": "Мысалы: shift_master",
        "btn_create_user": "ТІРКЕЛГІНІ САҚТАУ"
    },
    "ko": {
        "title": "SEOYON SUMMIT QAZAQ — 엔지니어링 어시스턴트",
        "subtitle": "엔지니어링 어시스턴트 및 지식 베이스 (SSQ ASSISTANT v3.0)",
        "tab_dash": "📊 메인 대시보드",
        "tab_planner": "📅 일일 일지 및 근무 로그",
        "tab_tasks": "📋 유지보수 작업 관리",
        "tab_search": "🔍 지식 베이스 빠른 검색",
        "tab_calc": "🧮 서비스 계산기 및 계측기",
        "total_tasks": "총 유지보수 작업",
        "in_progress": "진행 중인 작업",
        "critical_tasks": "긴급 점검 요청",
        "kb_articles": "지식 베이스 매뉴얼 수",
        "quick_actions": "🚀 빠른 실행 및 퀵 가이드",
        "active_tasks": "📌 기술팀 현재 활성 작업 목록",
        "line_status": "🏭 라인 가동 상태 및 등급",
        "roles_title": "👤 직무 권한 및 담당 영역 분담",
        "add_task_btn": "+ 신규 작업 등록",
        "add_material_btn": "➕ 지식 베이스 자료 추가",
        "add_user_btn": "➕ 신규 계정 추가",
        "change_pass_btn": "🔑 비밀번호 변경",
        "logout_btn": "🚪 로그아웃",
        "login_title": "SSQ 시스템 로그인",
        "select_account": "사용자 계정을 선택하십시오:",
        "password_label": "접속 비밀번호:",
        "login_submit": "시스템 로그인",
        "change_pass_title": "초기 비밀번호 변경",
        "change_pass_desc": "초기 비밀번호로 로그인하였습니다. 계정 보안을 위해 신규 비밀번호를 설정하십시오.",
        "new_pass_label": "신규 비밀번호:",
        "confirm_pass_label": "신규 비밀번호 확인:",
        "save_pass_btn": "비밀번호 저장",
        "cancel_btn": "❌ 취소 (메인 화면으로)",
        "search_ph": "검색어를 입력하십시오 (fanuc, cicon, loto, 토크, voc)...",
        "author_label": "작성자:",
        "shop_label": "라인 / 공정:",
        "assignee_label": "담당자:",
        "creator_label": "등록자:",
        "priority_label": "우선순위:",
        "status_label": "진행 상태:",
        "view_instruction": "매뉴얼 보기",
        "more_info": "상세 정보",
        "reg_tb": "안전 규정",
        "btn_save_planner": "근무 일지에 저장",
        "btn_create_task": "작업 저장",
        "btn_create_kb": "지식 베이스에 저장",
        "modal_task_title": "신규 유지보수 작업 등록",
        "modal_kb_title": "지식 베이스 매뉴얼 / 자료 등록",
        "modal_user_title": "신규 사용자 계정 등록",
        "lbl_kb_category": "카테고리:",
        "ph_kb_category": "예: 자동화 / 로봇 공학",
        "lbl_kb_title": "매뉴얼 / 문서 제목:",
        "ph_kb_title": "예: 150RT 펌프 점검 규정",
        "lbl_kb_tags": "키워드 (태그):",
        "ph_kb_tags": "예: 펌프 냉각탑 150rt 냉각",
        "lbl_kb_content": "매뉴얼 상세 내용:",
        "ph_kb_content": "단계별 정비 지침을 입력하십시오...",
        "lbl_user_name": "성명 / 직책:",
        "ph_user_name": "예: 반장 아누아르",
        "lbl_user_role": "아이콘 표기 직급:",
        "ph_user_role": "예: 👨‍🔧 교대 반장",
        "lbl_user_id": "로그인 ID:",
        "ph_user_id": "예: shift_master",
        "btn_create_user": "계정 생성"
    },
    "en": {
        "title": "SEOYON SUMMIT QAZAQ — Engineering Assistant",
        "subtitle": "ENGINEERING ASSISTANT & KNOWLEDGE BASE (SSQ ASSISTANT v3.0)",
        "tab_dash": "📊 MAIN DASHBOARD",
        "tab_planner": "📅 DAILY PLANNER & SHIFT LOG",
        "tab_tasks": "📋 MAINTENANCE TASKS & WORK ORDERS",
        "tab_search": "🔍 KNOWLEDGE BASE QUICK SEARCH",
        "tab_calc": "🧮 SERVICE CALCULATORS & INSTRUMENTATION",
        "total_tasks": "Total Maintenance Tasks",
        "in_progress": "Tasks In Progress",
        "critical_tasks": "Critical Work Orders",
        "kb_articles": "Knowledge Base Manuals",
        "quick_actions": "🚀 QUICK ACTIONS & EXPRESS CHEATSHEETS",
        "active_tasks": "📌 ACTIVE ENGINEERING WORK ORDERS",
        "line_status": "🏭 LINE OPERATION STATUS & CATEGORIES",
        "roles_title": "👤 RESPONSIBILITY MATRIX & AUTHORIZATION ZONES",
        "add_task_btn": "+ CREATE NEW TASK",
        "add_material_btn": "➕ ADD MATERIAL TO ASSISTANT",
        "add_user_btn": "➕ Add User Account",
        "change_pass_btn": "🔑 Password",
        "logout_btn": "🚪 Logout",
        "login_title": "SSQ SYSTEM AUTHENTICATION",
        "select_account": "Select User Account:",
        "password_label": "Access Password:",
        "login_submit": "LOGIN TO SYSTEM",
        "change_pass_title": "CHANGE DEFAULT PASSWORD",
        "change_pass_desc": "You logged in with a default password. Please set a permanent password for security.",
        "new_pass_label": "New Password:",
        "confirm_pass_label": "Confirm New Password:",
        "save_pass_btn": "SAVE NEW PASSWORD",
        "cancel_btn": "❌ Cancel (To Main Screen)",
        "search_ph": "Enter search keyword (fanuc, cicon, loto, torque, voc)...",
        "author_label": "Author:",
        "shop_label": "Shop / Line:",
        "assignee_label": "Assignee:",
        "creator_label": "Created By:",
        "priority_label": "Priority:",
        "status_label": "Status:",
        "view_instruction": "Open Manual",
        "more_info": "Details",
        "reg_tb": "HSE Protocol",
        "btn_save_planner": "SAVE TO SHIFT LOG",
        "btn_create_task": "SAVE TASK",
        "btn_create_kb": "SAVE MATERIAL TO ASSISTANT",
        "modal_task_title": "Create New Maintenance Task",
        "modal_kb_title": "Add Manual / Material to Assistant",
        "modal_user_title": "Create New User Account",
        "lbl_kb_category": "Category:",
        "ph_kb_category": "e.g., Automation & Robotics",
        "lbl_kb_title": "Article / Manual Title:",
        "ph_kb_title": "e.g., 150RT Pump Inspection Protocol",
        "lbl_kb_tags": "Keywords (Tags):",
        "ph_kb_tags": "e.g., pump cooling tower 150rt cooling",
        "lbl_kb_content": "Full Manual Text:",
        "ph_kb_content": "Enter detailed step-by-step instructions...",
        "lbl_user_name": "Full Name / Title:",
        "ph_user_name": "e.g., Shift Master Anuar",
        "lbl_user_role": "Icon Title Badge:",
        "ph_user_role": "e.g., 👨‍🔧 SHIFT MASTER",
        "lbl_user_id": "Login ID:",
        "ph_user_id": "e.g., shift_master",
        "btn_create_user": "SAVE ACCOUNT"
    }
}

def tr(text, lang):
    if not text:
        return ""
    text_str = str(text).strip()
    if text_str in TEXT_TRANSLATIONS and lang in TEXT_TRANSLATIONS[text_str]:
        return TEXT_TRANSLATIONS[text_str][lang]
    return text_str

def tr_kb_category(kb_item, lang):
    item_id = kb_item.get("id")
    if item_id in KB_TRANSLATIONS and "category" in KB_TRANSLATIONS[item_id]:
        return KB_TRANSLATIONS[item_id]["category"].get(lang, KB_TRANSLATIONS[item_id]["category"]["ru"])
    return tr(kb_item.get("category", ""), lang)

def tr_kb_title(kb_item, lang):
    item_id = kb_item.get("id")
    if item_id in KB_TRANSLATIONS and "title" in KB_TRANSLATIONS[item_id]:
        return KB_TRANSLATIONS[item_id]["title"].get(lang, KB_TRANSLATIONS[item_id]["title"]["ru"])
    return tr(kb_item.get("title", ""), lang)

def tr_kb_content(kb_item, lang):
    item_id = kb_item.get("id")
    if item_id in KB_TRANSLATIONS and "content" in KB_TRANSLATIONS[item_id]:
        return KB_TRANSLATIONS[item_id]["content"].get(lang, KB_TRANSLATIONS[item_id]["content"]["ru"])
    return tr(kb_item.get("content", ""), lang)

def get_user_display_name(username, lang, user_obj=None):
    if username in ROLE_LOCALIZATIONS:
        return ROLE_LOCALIZATIONS[username].get(lang, ROLE_LOCALIZATIONS[username]["ru"])
    if user_obj:
        title = user_obj.get("title_badge", "")
        display = user_obj.get("display_name", "")
        if not title or title.strip() == display.strip():
            return display or title or username
        return f"{title} — {display}"
    return username



LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ txt.login_title | safe }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b111a;
            --card-bg: #141c28;
            --border-color: #233146;
            --cyan-accent: #00f0ff;
        }
        body {
            background-color: var(--bg-dark);
            color: #e1e7ed;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        .login-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 35px;
            width: 100%;
            max-width: 450px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .brand-logo {
            text-align: center;
            margin-bottom: 25px;
        }
        .brand-logo h4 {
            font-weight: 800;
            color: #fff;
            letter-spacing: 1px;
            margin-bottom: 5px;
        }
        .brand-logo div {
            font-size: 11px;
            color: var(--cyan-accent);
            font-weight: 700;
            text-transform: uppercase;
        }
        .btn-cyan {
            background-color: var(--cyan-accent);
            color: #000;
            font-weight: 800;
            border: none;
            width: 100%;
            padding: 12px;
            margin-top: 10px;
        }
        .btn-cyan:hover {
            background-color: #00c4d4;
            color: #000;
        }
        .lang-picker {
            display: flex;
            justify-content: center;
            gap: 8px;
            margin-bottom: 20px;
        }
        .lang-btn {
            color: #8a99ad;
            border: 1px solid #233146;
            padding: 4px 12px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 700;
        }
        .lang-btn.active {
            color: #00f0ff;
            border-color: #00f0ff;
            background: rgba(0,240,255,0.1);
        }
    </style>
</head>
<body>

    <div class="login-card">
        <div class="lang-picker">
            <a href="javascript:void(0)" onclick="setLang('ru')" class="lang-btn {% if lang == 'ru' %}active{% endif %}">RU</a>
            <a href="javascript:void(0)" onclick="setLang('kk')" class="lang-btn {% if lang == 'kk' %}active{% endif %}">KK</a>
            <a href="javascript:void(0)" onclick="setLang('ko')" class="lang-btn {% if lang == 'ko' %}active{% endif %}">KO</a>
            <a href="javascript:void(0)" onclick="setLang('en')" class="lang-btn {% if lang == 'en' %}active{% endif %}">EN</a>
        </div>

        <div class="brand-logo">
            <h4>🛠️ SEOYON SUMMIT QAZAQ</h4>
            <div>{{ txt.subtitle | safe }}</div>
        </div>

        {% if error %}
        <div class="alert alert-danger py-2 small mb-3">{{ error }}</div>
        {% endif %}

        <form action="/login" method="POST">
            <div class="mb-3">
                <label class="form-label small fw-bold text-light">{{ txt.select_account | safe }}</label>
                <select name="username" class="form-select" required>
                    {% for u_key, u_val in users.items() %}
                    <option value="{{ u_key }}">{{ get_user_display_name(u_key, lang, u_val) }}</option>
                    {% endfor %}
                </select>
            </div>
            <div class="mb-3">
                <label class="form-label small fw-bold text-light">{{ txt.password_label | safe }}</label>
                <input type="password" name="password" class="form-control" placeholder="••••" required>
            </div>
            <button type="submit" class="btn btn-cyan">{{ txt.login_submit | safe }}</button>
        </form>

        <div class="mt-4 pt-3 border-top border-secondary text-center">
            <button class="btn btn-sm btn-outline-info text-cyan border-cyan" data-bs-toggle="modal" data-bs-target="#addUserModal">
                {{ txt.add_user_btn | safe }}
            </button>
        </div>
    </div>

    <!-- ADD USER MODAL -->
    <div class="modal fade" id="addUserModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold">{{ txt.modal_user_title | safe }}</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form action="/add_user" method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_user_name | safe }}</label>
                            <input type="text" name="display_name" class="form-control" required placeholder="{{ txt.ph_user_name | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_user_role | safe }}</label>
                            <input type="text" name="title_badge" class="form-control" required placeholder="{{ txt.ph_user_role | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_user_id | safe }}</label>
                            <input type="text" name="username" class="form-control" required placeholder="{{ txt.ph_user_id | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.password_label | safe }}</label>
                            <input type="password" name="password" class="form-control" value="1111" required>
                        </div>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ txt.cancel_btn | safe }}</button>
                        <button type="submit" class="btn btn-cyan">{{ txt.btn_create_user | safe }}</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        function setLang(lang) {
            window.location.href = '/change_lang/' + lang;
        }
    </script>

<!-- Google Translate Auto-Translation Integration -->
<div id="google_translate_element" style="display:none;"></div>
<script type="text/javascript">
    function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'ru',
            includedLanguages: 'ru,kk,ko,en',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');
    }

    function triggerAutoTranslate(langCode) {
        var gtCombo = document.querySelector('.goog-te-combo');
        if (gtCombo) {
            gtCombo.value = langCode;
            gtCombo.dispatchEvent(new Event('change'));
        } else {
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/; domain=' + window.location.hostname;
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/';
        }
    }

    // Auto-trigger on page load if language is not RU
    window.addEventListener('DOMContentLoaded', function() {
        var currentLang = "{{ lang }}";
        if (currentLang !== 'ru') {
            setTimeout(function() {
                triggerAutoTranslate(currentLang);
            }, 800);
        }
    });
</script>
<script type="text/javascript" src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

</body>
</html>
"""

CHANGE_PASSWORD_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ txt.change_pass_title | safe }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b111a;
            --card-bg: #141c28;
            --border-color: #233146;
            --cyan-accent: #00f0ff;
        }
        body {
            background-color: var(--bg-dark);
            color: #e1e7ed;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
            padding: 20px;
        }
        .pass-card {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 35px;
            width: 100%;
            max-width: 480px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }
        .btn-cyan {
            background-color: var(--cyan-accent);
            color: #000;
            font-weight: 800;
            border: none;
            width: 100%;
            padding: 12px;
            margin-top: 15px;
        }
    </style>
</head>
<body>
    <div class="pass-card">
        <h4 class="fw-bold text-light mb-2">🔑 {{ txt.change_pass_title | safe }}</h4>
        <p class="small text-muted mb-4">{{ txt.change_pass_desc | safe }}</p>

        {% if error %}
        <div class="alert alert-danger py-2 small mb-3">{{ error }}</div>
        {% endif %}

        <form action="/change_password" method="POST">
            <div class="mb-3">
                <label class="form-label small fw-bold text-light">{{ txt.new_pass_label | safe }}</label>
                <input type="password" name="new_password" class="form-control" placeholder="••••••••" required>
            </div>
            <div class="mb-3">
                <label class="form-label small fw-bold text-light">{{ txt.confirm_pass_label | safe }}</label>
                <input type="password" name="confirm_password" class="form-control" placeholder="••••••••" required>
            </div>
            <button type="submit" class="btn btn-cyan">{{ txt.save_pass_btn | safe }}</button>
            <a href="/cancel_password_change" class="btn btn-outline-secondary w-100 mt-2">{{ txt.cancel_btn | safe }}</a>
        </form>
    </div>

<!-- Google Translate Auto-Translation Integration -->
<div id="google_translate_element" style="display:none;"></div>
<script type="text/javascript">
    function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'ru',
            includedLanguages: 'ru,kk,ko,en',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');
    }

    function triggerAutoTranslate(langCode) {
        var gtCombo = document.querySelector('.goog-te-combo');
        if (gtCombo) {
            gtCombo.value = langCode;
            gtCombo.dispatchEvent(new Event('change'));
        } else {
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/; domain=' + window.location.hostname;
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/';
        }
    }

    // Auto-trigger on page load if language is not RU
    window.addEventListener('DOMContentLoaded', function() {
        var currentLang = "{{ lang }}";
        if (currentLang !== 'ru') {
            setTimeout(function() {
                triggerAutoTranslate(currentLang);
            }, 800);
        }
    });
</script>
<script type="text/javascript" src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

</body>
</html>
"""

MAIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ txt.title | safe }}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root {
            --bg-dark: #0b111a;
            --card-bg: #141c28;
            --border-color: #233146;
            --cyan-accent: #00f0ff;
            --green-accent: #00ff66;
            --yellow-accent: #ffdd00;
            --red-accent: #ff3366;
            --text-main: #e1e7ed;
            --text-muted: #8a99ad;
        }
        body {
            background-color: var(--bg-dark);
            color: var(--text-main);
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding-bottom: 40px;
        }
        .hero-banner {
            background: linear-gradient(135deg, #080d14 0%, #101926 100%);
            border-bottom: 2px solid var(--cyan-accent);
            padding: 18px 28px;
            margin-bottom: 20px;
            box-shadow: 0 4px 20px rgba(0,240,255,0.15);
        }
        .brand-title {
            font-size: 22px;
            font-weight: 800;
            letter-spacing: 1px;
            color: #fff;
        }
        .brand-subtitle {
            font-size: 11px;
            color: var(--cyan-accent);
            font-weight: 700;
            text-transform: uppercase;
        }
        .user-badge {
            background: rgba(0, 240, 255, 0.1);
            border: 1px solid var(--cyan-accent);
            color: var(--cyan-accent);
            padding: 6px 14px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 700;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }
        .nav-tabs-custom {
            border-bottom: 1px solid var(--border-color);
            margin-bottom: 25px;
        }
        .nav-tabs-custom .nav-link {
            color: var(--text-muted);
            border: none;
            border-bottom: 3px solid transparent;
            font-weight: 700;
            padding: 12px 20px;
            font-size: 14px;
            background: transparent;
            transition: all 0.2s;
        }
        .nav-tabs-custom .nav-link:hover {
            color: #fff;
            background: rgba(255,255,255,0.02);
        }
        .nav-tabs-custom .nav-link.active {
            color: var(--cyan-accent);
            border-bottom-color: var(--cyan-accent);
            background: rgba(0, 240, 255, 0.05);
        }
        .card-custom {
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        }
        .card-title-custom {
            font-size: 16px;
            font-weight: 700;
            color: #fff;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 10px;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .form-control, .form-select, textarea {
            background-color: #0d1520 !important;
            border: 1px solid var(--border-color) !important;
            color: #fff !important;
        }
        .form-control:focus, .form-select:focus {
            border-color: var(--cyan-accent) !important;
            box-shadow: 0 0 8px rgba(0,240,255,0.3) !important;
        }
        .btn-cyan {
            background-color: var(--cyan-accent);
            color: #000;
            font-weight: 700;
            border: none;
        }
        .btn-cyan:hover {
            background-color: #00c4d4;
            color: #000;
        }
        .search-box {
            position: relative;
        }
        .search-input {
            padding-left: 40px;
            font-size: 16px;
            height: 48px;
            border-radius: 24px;
        }
        .search-icon {
            position: absolute;
            left: 15px;
            top: 12px;
            font-size: 20px;
            color: var(--text-muted);
        }
        .kb-card {
            border-left: 4px solid var(--cyan-accent);
        }
        .stat-box {
            text-align: center;
            padding: 15px;
            background: #0d1520;
            border-radius: 6px;
            border: 1px solid var(--border-color);
        }
        .stat-num {
            font-size: 28px;
            font-weight: 800;
            color: var(--cyan-accent);
        }
        .stat-lbl {
            font-size: 12px;
            color: var(--text-muted);
            text-transform: uppercase;
            font-weight: 600;
        }
        .lang-btn {
            color: #8a99ad;
            border: 1px solid #233146;
            padding: 4px 10px;
            border-radius: 4px;
            text-decoration: none;
            font-size: 12px;
            font-weight: 700;
        }
        .lang-btn.active {
            color: #00f0ff;
            border-color: #00f0ff;
            background: rgba(0,240,255,0.1);
        }
    </style>
</head>
<body>

    <!-- Hero Banner & Navigation Header -->
    <div class="hero-banner">
        <div class="d-flex justify-content-between align-items-center flex-wrap">
            <div>
                <div class="brand-title">🛠️ SEOYON SUMMIT QAZAQ</div>
                <div class="brand-subtitle">{{ txt.subtitle | safe }}</div>
            </div>
            
            <div class="d-flex align-items-center gap-3 mt-2 mt-md-0">
                <div class="user-badge">
                    {{ current_user_name }}
                </div>
                
                <div>
                    <a href="javascript:void(0)" onclick="setLang('ru')" class="lang-btn {% if lang == 'ru' %}active{% endif %}">RU</a>
                    <a href="javascript:void(0)" onclick="setLang('kk')" class="lang-btn {% if lang == 'kk' %}active{% endif %}">KK</a>
                    <a href="javascript:void(0)" onclick="setLang('ko')" class="lang-btn {% if lang == 'ko' %}active{% endif %}">KO</a>
                    <a href="javascript:void(0)" onclick="setLang('en')" class="lang-btn {% if lang == 'en' %}active{% endif %}">EN</a>
                </div>

                <a href="/change_password" class="btn btn-sm btn-outline-info text-cyan border-cyan fw-bold">{{ txt.change_pass_btn | safe }}</a>
                <a href="/logout" class="btn btn-sm btn-outline-danger fw-bold">{{ txt.logout_btn | safe }}</a>
            </div>
        </div>
    </div>

    <div class="container-fluid px-4">
        
        <!-- Navigation Tabs -->
        <ul class="nav nav-tabs nav-tabs-custom" id="mainTabs" role="tablist">
            <li class="nav-item">
                <button class="nav-link active" id="tab-dash-btn" data-bs-toggle="tab" data-bs-target="#tab-dash" type="button">
                    {{ txt.tab_dash | safe }}
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link" id="tab-planner-btn" data-bs-toggle="tab" data-bs-target="#tab-planner" type="button">
                    {{ txt.tab_planner | safe }}
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link" id="tab-tasks-btn" data-bs-toggle="tab" data-bs-target="#tab-tasks" type="button">
                    {{ txt.tab_tasks | safe }} ({{ data.tasks|length }})
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link" id="tab-search-btn" data-bs-toggle="tab" data-bs-target="#tab-search" type="button">
                    {{ txt.tab_search | safe }}
                </button>
            </li>
            <li class="nav-item">
                <button class="nav-link" id="tab-calc-btn" data-bs-toggle="tab" data-bs-target="#tab-calc" type="button">
                    {{ txt.tab_calc | safe }}
                </button>
            </li>
        </ul>

        <div class="tab-content" id="mainTabContent">
            
            <!-- 1. DASHBOARD TAB -->
            <div class="tab-pane fade show active" id="tab-dash" role="tabpanel">
                <div class="row">
                    <div class="col-md-3">
                        <div class="stat-box">
                            <div class="stat-num">{{ data.tasks|length }}</div>
                            <div class="stat-lbl">{{ txt.total_tasks | safe }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box">
                            <div class="stat-num" style="color: var(--yellow-accent);">
                                {{ data.tasks | selectattr('status', 'equalto', 'В работе') | list | length }}
                            </div>
                            <div class="stat-lbl">{{ txt.in_progress | safe }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box">
                            <div class="stat-num" style="color: var(--red-accent);">
                                {{ data.tasks | selectattr('priority', 'equalto', 'Критический') | list | length }}
                            </div>
                            <div class="stat-lbl">{{ txt.critical_tasks | safe }}</div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="stat-box">
                            <div class="stat-num" style="color: var(--green-accent);">
                                {{ data.knowledge_base|length }}
                            </div>
                            <div class="stat-lbl">{{ txt.kb_articles | safe }}</div>
                        </div>
                    </div>
                </div>

                <div class="row mt-4">
                    <div class="col-md-8">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>{{ txt.quick_actions | safe }}</span>
                            </div>
                            <div class="row g-3">
                                <div class="col-md-6">
                                    <div class="p-3 bg-dark rounded border border-secondary">
                                        <h6 class="text-warning fw-bold">🤖 {{ tr_kb_title({'id': 'kb_fanuc'}, lang) }}</h6>
                                        <p class="small text-muted mb-2">T1 -> [SYSTEM] -> [Master/Cal] -> RES_PULSE -> RESET.</p>
                                        <button class="btn btn-sm btn-outline-warning w-100 fw-bold" onclick="openKnowledgeModal('kb_fanuc')">{{ txt.view_instruction | safe }}</button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 bg-dark rounded border border-secondary">
                                        <h6 class="text-info fw-bold">💻 {{ tr_kb_title({'id': 'kb_cicon'}, lang) }}</h6>
                                        <p class="small text-muted mb-2">Bar = (mA - 4.0) / 16.0 * Max_Bar. 12.0 mA = 125.0 bar.</p>
                                        <button class="btn btn-sm btn-outline-info w-100 fw-bold" onclick="openKnowledgeModal('kb_cicon')">{{ txt.view_instruction | safe }}</button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 bg-dark rounded border border-secondary">
                                        <h6 class="text-success fw-bold">🔧 {{ tr_kb_title({'id': 'kb_torque'}, lang) }}</h6>
                                        <p class="small text-muted mb-2">5.5 kgf/cm², 3 measurements, 45.0 N·m.</p>
                                        <button class="btn btn-sm btn-outline-success w-100 fw-bold" onclick="openKnowledgeModal('kb_torque')">{{ txt.more_info | safe }}</button>
                                    </div>
                                </div>
                                <div class="col-md-6">
                                    <div class="p-3 bg-dark rounded border border-secondary">
                                        <h6 class="text-danger fw-bold">🔒 {{ tr_kb_title({'id': 'kb_loto'}, lang) }}</h6>
                                        <p class="small text-muted mb-2">Shutdown -> Circuit Breaker -> Pressure Release -> Lock/Tag -> Zero Energy.</p>
                                        <button class="btn btn-sm btn-outline-danger w-100 fw-bold" onclick="openKnowledgeModal('kb_loto')">{{ txt.reg_tb | safe }}</button>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>{{ txt.active_tasks | safe }}</span>
                            </div>
                            <div class="table-responsive">
                                <table class="table table-dark table-hover align-middle">
                                    <thead>
                                        <tr>
                                            <th>{{ txt.tab_tasks | safe }}</th>
                                            <th>{{ txt.shop_label | safe }}</th>
                                            <th>{{ txt.assignee_label | safe }}</th>
                                            <th>{{ txt.priority_label | safe }}</th>
                                            <th>{{ txt.status_label | safe }}</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {% for t in data.tasks %}
                                        <tr>
                                            <td class="fw-bold">{{ tr(t.title, lang) }}</td>
                                            <td><span class="badge bg-secondary">{{ tr(t.shop, lang) }}</span></td>
                                            <td>{{ get_user_display_name(t.assignee, lang) }}</td>
                                            <td><span class="badge bg-warning text-dark fw-bold">{{ tr(t.priority, lang) }}</span></td>
                                            <td><span class="badge bg-info text-dark fw-bold">{{ tr(t.status, lang) }}</span></td>
                                        </tr>
                                        {% endfor %}
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-4">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>{{ txt.line_status | safe }}</span>
                            </div>
                            <ul class="list-group list-group-flush bg-transparent">
                                <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
                                    <span>Seat Foaming Line</span>
                                    <span class="badge bg-success">RUN (Cat. A)</span>
                                </li>
                                <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
                                    <span>H_Lin'g Board Line</span>
                                    <span class="badge bg-success">RUN (Cat. A)</span>
                                </li>
                                <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
                                    <span>Floor Carpet Line</span>
                                    <span class="badge bg-success">RUN (Cat. A)</span>
                                </li>
                                <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
                                    <span>Utility (MAIN AIR 5.5 bar)</span>
                                    <span class="badge bg-info">ONLINE (Cat. B)</span>
                                </li>
                                <li class="list-group-item bg-transparent text-light border-secondary d-flex justify-content-between align-items-center">
                                    <span>VOC Tower (2.5t Carbon)</span>
                                    <span class="badge bg-info">96.5% (Cat. B)</span>
                                </li>
                            </ul>
                        </div>

                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>{{ txt.roles_title | safe }}</span>
                            </div>
                            <div class="small">
                                <p class="mb-2"><b class="text-warning">👑 {{ get_user_display_name('chief_engineer', lang) }}:</b> <span class="text-light">{{ tr_kb_content({'id': 'kb_roles'}, lang).split('\n')[0] }}</span></p>
                                <p class="mb-2"><b class="text-success">🔧 {{ get_user_display_name('chief_mechanic', lang) }}:</b> <span class="text-light">{{ tr_kb_content({'id': 'kb_roles'}, lang).split('\n')[1] if '\n' in tr_kb_content({'id': 'kb_roles'}, lang) else '' }}</span></p>
                                <p class="mb-0"><b class="text-info">⚡ {{ get_user_display_name('electronics_engineer', lang) }}:</b> <span class="text-light">{{ tr_kb_content({'id': 'kb_roles'}, lang).split('\n')[2] if '\n' in tr_kb_content({'id': 'kb_roles'}, lang) else '' }}</span></p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- 2. PLANNER TAB -->
            <div class="tab-pane fade" id="tab-planner" role="tabpanel">
                <div class="row">
                    <div class="col-md-5">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>📝 {{ txt.tab_planner | safe }}</span>
                            </div>
                            <form action="/add_planner" method="POST">
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Date:</label>
                                    <input type="date" name="date" class="form-control" value="2026-10-29" required>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Shift:</label>
                                    <select name="shift" class="form-select">
                                        <option value="Дневная смена (08:00 - 17:00)">{{ tr("Дневная смена (08:00 - 17:00)", lang) }}</option>
                                        <option value="Вечерняя смена (17:00 - 01:00)">{{ tr("Вечерняя смена (17:00 - 01:00)", lang) }}</option>
                                        <option value="Ночная смена (01:00 - 08:00)">{{ tr("Ночная смена (01:00 - 08:00)", lang) }}</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">{{ txt.author_label | safe }}</label>
                                    <input type="text" class="form-control" value="{{ current_user_name }}" readonly>
                                </div>
                                <div class="mb-3 form-check">
                                    <input type="checkbox" name="loto_checked" class="form-check-input" id="lotoCheck" checked>
                                    <label class="form-check-label small text-warning fw-bold" for="lotoCheck">LOTO & HSE Check Passed</label>
                                </div>
                                <div class="mb-3">
                                    <label class="form-label small fw-bold">Shift Notes:</label>
                                    <textarea name="content" class="form-control" rows="4" required></textarea>
                                </div>
                                <button type="submit" class="btn btn-cyan w-100">{{ txt.btn_save_planner | safe }}</button>
                            </form>
                        </div>
                    </div>

                    <div class="col-md-7">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>📖 SHIFT LOG HISTORY</span>
                            </div>
                            {% for p in data.planner_notes %}
                            <div class="p-3 mb-3 rounded border border-secondary bg-dark">
                                <div class="d-flex justify-content-between align-items-center mb-2">
                                    <span class="badge bg-cyan text-dark font-monospace fw-bold">{{ p.date }}</span>
                                    <span class="badge bg-secondary">{{ tr(p.shift, lang) }}</span>
                                    <span class="text-info fw-bold">✍️ {{ txt.author_label | safe }} {{ get_user_display_name(p.author, lang) }}</span>
                                    {% if p.loto_checked %}
                                        <span class="badge bg-success">🔒 LOTO OK</span>
                                    {% endif %}
                                </div>
                                <p class="mb-0 text-light" style="white-space: pre-line;">{{ tr(p.content, lang) }}</p>
                            </div>
                            {% endfor %}
                        </div>
                    </div>
                </div>
            </div>

            <!-- 3. TASKS TAB -->
            <div class="tab-pane fade" id="tab-tasks" role="tabpanel">
                <div class="row mb-3">
                    <div class="col-md-12 d-flex justify-content-between align-items-center">
                        <h5 class="fw-bold text-light mb-0">{{ txt.tab_tasks | safe }}</h5>
                        <button class="btn btn-cyan" data-bs-toggle="modal" data-bs-target="#addTaskModal">{{ txt.add_task_btn | safe }}</button>
                    </div>
                </div>

                <div class="row">
                    {% for t in data.tasks %}
                    <div class="col-md-6 mb-3">
                        <div class="card-custom h-100">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="fw-bold text-light mb-0">#{{ t.id }}. {{ tr(t.title, lang) }}</h6>
                                <span class="badge bg-warning text-dark fw-bold">{{ tr(t.priority, lang) }}</span>
                            </div>
                            <p class="small text-muted mb-2">{{ tr(t.desc, lang) }}</p>
                            <div class="d-flex justify-content-between align-items-center mt-3 pt-2 border-top border-secondary">
                                <span class="small text-info">🏭 {{ tr(t.shop, lang) }} | 👤 {{ get_user_display_name(t.assignee, lang) }}</span>
                                <div>
                                    <form action="/update_task_status" method="POST" class="d-inline">
                                        <input type="hidden" name="task_id" value="{{ t.id }}">
                                        <select name="status" class="form-select form-select-sm d-inline-block w-auto" onchange="this.form.submit()">
                                            <option value="Новая" {% if t.status == 'Новая' %}selected{% endif %}>{{ tr('Новая', lang) }}</option>
                                            <option value="В работе" {% if t.status == 'В работе' %}selected{% endif %}>{{ tr('В работе', lang) }}</option>
                                            <option value="Выполнено" {% if t.status == 'Выполнено' %}selected{% endif %}>{{ tr('Выполнено', lang) }}</option>
                                        </select>
                                    </form>
                                </div>
                            </div>
                        </div>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <!-- 4. SEARCH & KNOWLEDGE BASE TAB -->
            <div class="tab-pane fade" id="tab-search" role="tabpanel">
                <div class="card-custom">
                    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                        <div class="search-box flex-grow-1">
                            <span class="search-icon">🔍</span>
                            <input type="text" id="searchInput" class="form-control search-input" placeholder="{{ txt.search_ph | safe }}" onkeyup="filterKnowledge()">
                        </div>
                        <button class="btn btn-cyan" data-bs-toggle="modal" data-bs-target="#addKbModal">
                            {{ txt.add_material_btn | safe }}
                        </button>
                    </div>

                    <div id="kbList">
                        {% for kb in data.knowledge_base %}
                        <div class="kb-card card-custom mb-3 search-item" data-tags="{{ kb.tags }} {{ tr_kb_title(kb, lang)|lower }} {{ tr_kb_category(kb, lang)|lower }}">
                            <div class="d-flex justify-content-between align-items-center mb-2">
                                <span class="badge bg-info text-dark font-monospace fw-bold">{{ tr_kb_category(kb, lang) }}</span>
                                <span class="small text-muted">✍️ {{ txt.author_label | safe }} {{ get_user_display_name(kb.author, lang) }}</span>
                            </div>
                            <h5 class="fw-bold text-light">{{ tr_kb_title(kb, lang) }}</h5>
                            <p class="text-light style-content mb-0" style="white-space: pre-line;">{{ tr_kb_content(kb, lang) }}</p>
                        </div>
                        {% endfor %}
                    </div>
                </div>
            </div>

            <!-- 5. CALCULATORS TAB -->
            <div class="tab-pane fade" id="tab-calc" role="tabpanel">
                <div class="row">
                    <div class="col-md-6">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>💻 CICON PLC 4-20mA SCALING CALCULATOR</span>
                            </div>
                            <p class="small text-muted">Bar = (mA - 4.0) / 16.0 * Max_Bar</p>
                            <div class="mb-3">
                                <label class="form-label small">Sensor Current (mA):</label>
                                <input type="number" step="0.1" id="calcMA" class="form-control" value="12.0" oninput="calculatePLC()">
                            </div>
                            <div class="mb-3">
                                <label class="form-label small">Max Range (at 20 mA):</label>
                                <input type="number" step="1" id="calcMax" class="form-control" value="250" oninput="calculatePLC()">
                            </div>
                            <div class="p-3 bg-dark rounded border border-info text-center">
                                <div class="small text-muted">Calculated Pressure:</div>
                                <div class="fs-2 fw-bold text-cyan" id="calcResult">125.0 bar</div>
                            </div>
                        </div>
                    </div>

                    <div class="col-md-6">
                        <div class="card-custom">
                            <div class="card-title-custom">
                                <span>🔧 IMPACT WRENCH TORQUE CALIBRATION</span>
                            </div>
                            <p class="small text-muted">M_avg calculation (Target: 45.0 N·m at 5.5 kgf/cm²)</p>
                            <div class="row g-2 mb-3">
                                <div class="col-4">
                                    <label class="form-label small">Measure 1:</label>
                                    <input type="number" step="0.1" id="m1" class="form-control" value="44.8" oninput="calculateTorque()">
                                </div>
                                <div class="col-4">
                                    <label class="form-label small">Measure 2:</label>
                                    <input type="number" step="0.1" id="m2" class="form-control" value="45.2" oninput="calculateTorque()">
                                </div>
                                <div class="col-4">
                                    <label class="form-label small">Measure 3:</label>
                                    <input type="number" step="0.1" id="m3" class="form-control" value="45.0" oninput="calculateTorque()">
                                </div>
                            </div>
                            <div class="p-3 bg-dark rounded border border-success text-center">
                                <div class="small text-muted">Average Torque:</div>
                                <div class="fs-2 fw-bold text-success" id="torqueResult">45.0 N·m (OK)</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </div>

    <!-- VIEW KNOWLEDGE MODAL -->
    <div class="modal fade" id="viewKbModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold text-cyan" id="viewKbTitle"></h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <div class="p-3 bg-dark rounded border border-secondary text-light style-content" id="viewKbContent" style="white-space: pre-line; font-size: 15px; line-height: 1.6;"></div>
                </div>
                <div class="modal-footer border-secondary">
                    <button type="button" class="btn btn-cyan btn-sm" onclick="copyKbText()">📋 Copy Text</button>
                    <button type="button" class="btn btn-secondary btn-sm" data-bs-dismiss="modal">{{ txt.cancel_btn | safe }}</button>
                </div>
            </div>
        </div>
    </div>

    <!-- ADD TASK MODAL -->
    <div class="modal fade" id="addTaskModal" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold">{{ txt.modal_task_title | safe }}</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form action="/add_task" method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.tab_tasks | safe }}:</label>
                            <input type="text" name="title" class="form-control" required>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.shop_label | safe }}</label>
                            <select name="shop" class="form-select">
                                <option value="Seat Foaming Line">Seat Foaming Line</option>
                                <option value="H_Lin'g Line">H_Lin'g Line</option>
                                <option value="Floor Carpet Line">Floor Carpet Line</option>
                                <option value="Utility & Ecology">Utility & Ecology</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.assignee_label | safe }}</label>
                            <select name="assignee" class="form-select">
                                {% for u_key, u_val in data.users.items() %}
                                <option value="{{ u_key }}">{{ get_user_display_name(u_key, lang, u_val) }}</option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.priority_label | safe }}</label>
                            <select name="priority" class="form-select">
                                <option value="Критический">{{ tr("Критический", lang) }}</option>
                                <option value="Высокий">{{ tr("Высокий", lang) }}</option>
                                <option value="Средний" selected>{{ tr("Средний", lang) }}</option>
                                <option value="Низкий">{{ tr("Низкий", lang) }}</option>
                            </select>
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">Description:</label>
                            <textarea name="desc" class="form-control" rows="3"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ txt.cancel_btn | safe }}</button>
                        <button type="submit" class="btn btn-cyan">{{ txt.btn_create_task | safe }}</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <!-- ADD KB MODAL -->
    <div class="modal fade" id="addKbModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content bg-dark text-light border-secondary">
                <div class="modal-header border-secondary">
                    <h5 class="modal-title fw-bold">{{ txt.modal_kb_title | safe }}</h5>
                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                </div>
                <form action="/add_kb" method="POST">
                    <div class="modal-body">
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_kb_category | safe }}</label>
                            <input type="text" name="category" class="form-control" required placeholder="{{ txt.ph_kb_category | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_kb_title | safe }}</label>
                            <input type="text" name="title" class="form-control" required placeholder="{{ txt.ph_kb_title | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_kb_tags | safe }}</label>
                            <input type="text" name="tags" class="form-control" placeholder="{{ txt.ph_kb_tags | safe }}">
                        </div>
                        <div class="mb-3">
                            <label class="form-label small fw-bold">{{ txt.lbl_kb_content | safe }}</label>
                            <textarea name="content" class="form-control" rows="6" required placeholder="{{ txt.ph_kb_content | safe }}"></textarea>
                        </div>
                    </div>
                    <div class="modal-footer border-secondary">
                        <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">{{ txt.cancel_btn | safe }}</button>
                        <button type="submit" class="btn btn-cyan">{{ txt.btn_create_kb | safe }}</button>
                    </div>
                </form>
            </div>
        </div>
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        var kbData = {
            'kb_fanuc': {
                'title': {{ ('🤖 ' + tr_kb_title({"id": "kb_fanuc"}, lang)) | tojson }},
                'content': {{ tr_kb_content({"id": "kb_fanuc"}, lang) | tojson }}
            },
            'kb_cicon': {
                'title': {{ ('💻 ' + tr_kb_title({"id": "kb_cicon"}, lang)) | tojson }},
                'content': {{ tr_kb_content({"id": "kb_cicon"}, lang) | tojson }}
            },
            'kb_torque': {
                'title': {{ ('🔧 ' + tr_kb_title({"id": "kb_torque"}, lang)) | tojson }},
                'content': {{ tr_kb_content({"id": "kb_torque"}, lang) | tojson }}
            },
            'kb_loto': {
                'title': {{ ('🔒 ' + tr_kb_title({"id": "kb_loto"}, lang)) | tojson }},
                'content': {{ tr_kb_content({"id": "kb_loto"}, lang) | tojson }}
            }
        };

        function setLang(lang) {
            var currentTab = localStorage.getItem('ssq_active_tab') || 'tab-dash-btn';
            window.location.href = '/change_lang/' + lang + '?tab=' + currentTab;
        }

        function openTab(tabBtnId) {
            var btn = document.getElementById(tabBtnId);
            if (btn) {
                var tab = new bootstrap.Tab(btn);
                tab.show();
                localStorage.setItem('ssq_active_tab', tabBtnId);
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            var tabButtons = document.querySelectorAll('#mainTabs button[data-bs-toggle="tab"]');
            tabButtons.forEach(function(btn) {
                btn.addEventListener('shown.bs.tab', function(e) {
                    localStorage.setItem('ssq_active_tab', e.target.id);
                });
            });

            var activeTab = "{{ active_tab }}" || localStorage.getItem('ssq_active_tab') || 'tab-dash-btn';
            openTab(activeTab);
        });

        function openKnowledgeModal(id) {
            if (kbData[id]) {
                document.getElementById('viewKbTitle').innerText = kbData[id].title;
                document.getElementById('viewKbContent').innerText = kbData[id].content;
                var myModal = new bootstrap.Modal(document.getElementById('viewKbModal'));
                myModal.show();
            }
        }

        function filterKnowledge() {
            var query = document.getElementById("searchInput").value.toLowerCase().trim();
            var items = document.querySelectorAll(".search-item");
            items.forEach(function(item) {
                var tags = item.getAttribute("data-tags") || "";
                if (tags.toLowerCase().indexOf(query) !== -1 || query === "") {
                    item.style.display = "block";
                } else {
                    item.style.display = "none";
                }
            });
        }

        function calculatePLC() {
            var ma = parseFloat(document.getElementById("calcMA").value) || 0;
            var maxVal = parseFloat(document.getElementById("calcMax").value) || 0;
            var val = ((ma - 4.0) / 16.0) * maxVal;
            if (val < 0) val = 0;
            document.getElementById("calcResult").innerText = val.toFixed(1) + " bar / °C";
        }

        function calculateTorque() {
            var m1 = parseFloat(document.getElementById("m1").value) || 0;
            var m2 = parseFloat(document.getElementById("m2").value) || 0;
            var m3 = parseFloat(document.getElementById("m3").value) || 0;
            var avg = (m1 + m2 + m3) / 3.0;
            var status = "OK";
            if (Math.abs(avg - 45.0) > 1.5) {
                status = "CALIBRATION NEEDED";
            }
            document.getElementById("torqueResult").innerText = avg.toFixed(1) + " N·m (" + status + ")";
        }

        function copyKbText() {
            var text = document.getElementById("viewKbContent").innerText;
            navigator.clipboard.writeText(text).then(function() {
                alert("Copied!");
            });
        }
    </script>

<!-- Google Translate Auto-Translation Integration -->
<div id="google_translate_element" style="display:none;"></div>
<script type="text/javascript">
    function googleTranslateElementInit() {
        new google.translate.TranslateElement({
            pageLanguage: 'ru',
            includedLanguages: 'ru,kk,ko,en',
            layout: google.translate.TranslateElement.InlineLayout.SIMPLE,
            autoDisplay: false
        }, 'google_translate_element');
    }

    function triggerAutoTranslate(langCode) {
        var gtCombo = document.querySelector('.goog-te-combo');
        if (gtCombo) {
            gtCombo.value = langCode;
            gtCombo.dispatchEvent(new Event('change'));
        } else {
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/; domain=' + window.location.hostname;
            document.cookie = 'googtrans=/ru/' + langCode + '; path=/';
        }
    }

    // Auto-trigger on page load if language is not RU
    window.addEventListener('DOMContentLoaded', function() {
        var currentLang = "{{ lang }}";
        if (currentLang !== 'ru') {
            setTimeout(function() {
                triggerAutoTranslate(currentLang);
            }, 800);
        }
    });
</script>
<script type="text/javascript" src="https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"></script>

</body>
</html>
"""

@app.route("/")
def index():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    lang = session.get("lang", "ru")
    txt = I18N.get(lang, I18N["ru"])
    active_tab = request.args.get("tab", "tab-dash-btn")
    current_user_name = get_user_display_name(session["username"], lang, data["users"].get(session["username"]))
    return render_template_string(
        MAIN_TEMPLATE,
        data=data,
        current_user_name=current_user_name,
        lang=lang,
        txt=txt,
        active_tab=active_tab,
        tr=tr,
        tr_kb_category=tr_kb_category,
        tr_kb_title=tr_kb_title,
        tr_kb_content=tr_kb_content,
        get_user_display_name=get_user_display_name
    )

@app.route("/login", methods=["GET", "POST"])
def login():
    data = load_data()
    lang = session.get("lang", "ru")
    txt = I18N.get(lang, I18N["ru"])
    error = None
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        users = data.get("users", DEFAULT_USERS)
        if username in users and users[username]["password"] == password:
            session["username"] = username
            if users[username].get("must_change", False):
                return redirect(url_for("change_password"))
            return redirect(url_for("index"))
        else:
            error = "Неверный пароль!" if lang == "ru" else "Қате құпия сөз!" if lang == "kk" else "비밀번호가 올바르지 않습니다!" if lang == "ko" else "Incorrect password!"
    return render_template_string(
        LOGIN_TEMPLATE,
        users=data.get("users", DEFAULT_USERS),
        error=error,
        lang=lang,
        txt=txt,
        get_user_display_name=get_user_display_name
    )

@app.route("/change_password", methods=["GET", "POST"])
def change_password():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    lang = session.get("lang", "ru")
    txt = I18N.get(lang, I18N["ru"])
    error = None
    if request.method == "POST":
        new_pass = request.form.get("new_password")
        confirm_pass = request.form.get("confirm_password")
        if not new_pass or new_pass != confirm_pass:
            error = "Пароли не совпадают!" if lang == "ru" else "Құпия сөздер сәйкес келмейді!" if lang == "kk" else "비밀번호가 일치하지 않습니다!" if lang == "ko" else "Passwords do not match!"
        else:
            username = session["username"]
            if "users" not in data:
                data["users"] = DEFAULT_USERS.copy()
            if username in data["users"]:
                data["users"][username]["password"] = new_pass
                data["users"][username]["must_change"] = False
            save_data(data)
            return redirect(url_for("index"))
    return render_template_string(CHANGE_PASSWORD_TEMPLATE, error=error, lang=lang, txt=txt)

@app.route("/cancel_password_change")
def cancel_password_change():
    if "username" in session:
        data = load_data()
        username = session["username"]
        if "users" in data and username in data["users"]:
            data["users"][username]["must_change"] = False
            save_data(data)
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/change_lang/<lang>")
def change_lang(lang):
    if lang in ["ru", "kk", "ko", "en"]:
        session["lang"] = lang
    tab = request.args.get("tab", "tab-dash-btn")
    return redirect(url_for("index", tab=tab))

@app.route("/add_user", methods=["POST"])
def add_user():
    data = load_data()
    username = request.form.get("username").strip()
    display_name = request.form.get("display_name").strip()
    title_badge = request.form.get("title_badge").strip()
    password = request.form.get("password").strip() or "1111"
    if "users" not in data:
        data["users"] = DEFAULT_USERS.copy()
    data["users"][username] = {
        "username": username,
        "display_name": display_name,
        "title_badge": title_badge or "👤 SPECIALIST",
        "password": password,
        "must_change": True
    }
    save_data(data)
    session["username"] = username
    return redirect(url_for("change_password"))

@app.route("/add_planner", methods=["POST"])
def add_planner():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    new_note = {
        "id": len(data["planner_notes"]) + 1,
        "date": request.form.get("date"),
        "shift": request.form.get("shift"),
        "author": session["username"],
        "loto_checked": "loto_checked" in request.form,
        "content": request.form.get("content")
    }
    data["planner_notes"].insert(0, new_note)
    save_data(data)
    return redirect(url_for("index", tab="tab-planner-btn"))

@app.route("/add_task", methods=["POST"])
def add_task():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    new_task = {
        "id": len(data["tasks"]) + 1,
        "title": request.form.get("title"),
        "shop": request.form.get("shop"),
        "assignee": request.form.get("assignee"),
        "created_by": session["username"],
        "priority": request.form.get("priority"),
        "status": "Новая",
        "due": datetime.datetime.now().strftime("%Y-%m-%d"),
        "desc": request.form.get("desc")
    }
    data["tasks"].insert(0, new_task)
    save_data(data)
    return redirect(url_for("index", tab="tab-tasks-btn"))

@app.route("/add_kb", methods=["POST"])
def add_kb():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    new_kb = {
        "id": "kb_" + str(int(time.time())),
        "category": request.form.get("category"),
        "title": request.form.get("title"),
        "tags": request.form.get("tags"),
        "author": session["username"],
        "content": request.form.get("content")
    }
    data["knowledge_base"].insert(0, new_kb)
    save_data(data)
    return redirect(url_for("index", tab="tab-search-btn"))

@app.route("/update_task_status", methods=["POST"])
def update_task_status():
    if "username" not in session:
        return redirect(url_for("login"))
    data = load_data()
    task_id = int(request.form.get("task_id", 0))
    new_status = request.form.get("status")
    for t in data["tasks"]:
        if t["id"] == task_id:
            t["status"] = new_status
            break
    save_data(data)
    return redirect(url_for("index", tab="tab-tasks-btn"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050, debug=False)