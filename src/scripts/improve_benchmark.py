import os
import sys
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.config import BENCHMARK_PATH


def improve_benchmark():
    with open(BENCHMARK_PATH, 'r', encoding='utf-8') as f:
        benchmark = json.load(f)

    improvements = {
        1: "26 августа 1993 года.", 
        4: "100% обыкновенных акций АО «Транснефтепродукт».", 
        5: "Еще 2 раза: в 2017 и 2018 годах.", 
        16: "Департамент внутреннего аудита и анализа основных направлений.",  
        19: "Строительство резервуаров на узловых нефтеперекачивающих станциях.",  
        20: "Увеличение емкости резервуарных парков для обеспечения сохранения качественных показателей нефти.",
        24: "Диверсификация поставок нефти в Западную Европу за счет перераспределения отгрузок нефти с зарубежных портов в российский порт на Балтийском море.",
        33: "Почти 19,2 тыс. км.",
        39: "Организация работы по обеспечению охраны окружающей среды в районах размещения объектов трубопроводного транспорта."
    }

    for triplet_id, improved_answer in improvements.items():
        for item in benchmark:
            if item['triplet_id'] == triplet_id:
                item['answer'] = improved_answer
                print(f"Улучшен вопрос {triplet_id}: {improved_answer}")
                break

    improved_path = BENCHMARK_PATH.replace('.json', '_improved.json')
    with open(improved_path, 'w', encoding='utf-8') as f:
        json.dump(benchmark, f, ensure_ascii=False, indent=2)

    print(f"Улучшенный бенчмарк сохранен: {improved_path}")
    return improved_path


if __name__ == "__main__":
    improve_benchmark()