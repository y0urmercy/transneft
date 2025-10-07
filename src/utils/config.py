import os

# ==================== ПУТИ К ФАЙЛАМ ====================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Данные
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

# Модели
MODELS_DIR = os.path.join(BASE_DIR, "models")
VECTOR_STORE_DIR = "vector_store_temp"

# Файлы
DOCUMENT_PATH = os.path.join(RAW_DATA_DIR, "Реестр данных о компании ПАО Транснефть для хакатона весна-лета 2026.docx")
BENCHMARK_PATH = os.path.join(PROCESSED_DATA_DIR, "transneft_qa_benchmark_final_40.json")
CHUNKS_PATH = os.path.join(PROCESSED_DATA_DIR, "document_chunks.json")
ELEMENTS_PATH = os.path.join(PROCESSED_DATA_DIR, "document_elements.json")

# ==================== ПАРАМЕТРЫ МОДЕЛИ ====================
MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
EMBEDDING_DIMENSION = 768
TOP_K_RESULTS = 8
SIMILARITY_THRESHOLD = 0.3

# ==================== ПАРАМЕТРЫ ОБРАБОТКИ ====================
MAX_CHUNK_SIZE = 400
MIN_CHUNK_SIZE = 50
MAX_WORDS_PER_CHUNK = 300

# ==================== КЛЮЧЕВЫЕ РАЗДЕЛЫ ====================
SECTION_HEADERS = [
    "Основные направления деятельности",
    "Уставный капитал. Акции",
    "Информация",
    "Проекты",
    "История",
    "Корпоративное управление",
    "Устав и внутренние документы",
    "Факты"
]

# ==================== КЛЮЧЕВЫЕ ФАКТЫ ====================
KEY_FACTS = {
    "акции": "724 934 300",
    "дата регистрации": "26.08.1993",
    "аудитор": "Акционерное общество «Кэпт»",
    "держатель реестра": "Независимая регистраторская компания Р.О.С.Т."
}


# ==================== СОЗДАНИЕ ДИРЕКТОРИЙ ====================
def create_directories():
    """Создает необходимые директории"""
    directories = [
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        MODELS_DIR,
        VECTOR_STORE_DIR
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Создана директория: {directory}")


# Создаем директории при импорте
create_directories()