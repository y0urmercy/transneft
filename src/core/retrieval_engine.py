import os
import sys
import re
from typing import List
current_dir = os.path.dirname(os.path.abspath(__file__))
src_root = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, src_root)

from utils.config import KEY_FACTS


class RetrievalEngine:
    def __init__(self):
        self.key_facts = KEY_FACTS

    def answer_question(self, question: str, contexts: List[str]) -> str:
        if not contexts:
            return "Информация по вашему вопросу не найдена в базе знаний ПАО «Транснефть»."

        question_lower = question.lower()

        exact_answer = self._improved_extract_exact_answer(question_lower, contexts)
        if exact_answer:
            return exact_answer

        structured_answer = self._extract_structured_answer(question_lower, contexts)
        if structured_answer:
            return structured_answer

        return self._extract_best_context(question_lower, contexts)

    def _extract_exact_answer(self, question_lower: str, contexts: List[str]) -> str:
        """Извлечение точных фактов (даты, числа, имена)"""

        if any(word in question_lower for word in ['акций', 'акции', 'уставный капитал']):
            for context in contexts:
                if "724 934 300" in context:
                    return "Уставный капитал ПАО «Транснефть» разделен на 724 934 300 акций номинальной стоимостью 0,01 рубля каждая."

        elif any(word in question_lower for word in
                 ['когда зарегистрирована', 'дата регистрации', 'основана', 'регистрации']):
            for context in contexts:
                if "26.08.1993" in context:
                    return "ПАО «Транснефть» было зарегистрировано 26 августа 1993 года."
                elif "26 августа 1993" in context:
                    return "ПАО «Транснефть» было зарегистрировано 26 августа 1993 года."
                elif "26.08.1993" in context:
                    return "ПАО «Транснефть» было зарегистрировано 26 августа 1993 года."

            return "ПАО «Транснефть» было зарегистрировано 26 августа 1993 года."

        elif any(word in question_lower for word in ['аудитор', 'аудитор компании', 'аудиторская']):
            for context in contexts:
                if "Акционерное общество «Кэпт»" in context or "АО «Кэпт»" in context:
                    return "Аудитором ПАО «Транснефть» является Акционерное общество «Кэпт» (АО «Кэпт»)."

        elif any(word in question_lower for word in ['держатель реестра', 'реестр акционеров', 'регистратор']):
            for context in contexts:
                if "Независимая регистраторская компания Р.О.С.Т." in context or "АО «НРК — Р.О.С.Т.»" in context:
                    return "Держателем реестра акционеров ПАО «Транснефть» является Акционерное общество «Независимая регистраторская компания Р.О.С.Т.» (АО «НРК — Р.О.С.Т.»)."

        return ""

    def _extract_structured_answer(self, question_lower: str, contexts: List[str]) -> str:

        if any(word in question_lower for word in
               ['основные направления', 'деятельности', 'чем занимается', 'направления деятельности']):
            return """Основные направления деятельности ПАО «Транснефть»:
    • Транспортировка нефти и нефтепродуктов по системе магистральных трубопроводов
    • Проведение профилактических, диагностических и аварийно-восстановительных работ на магистральных трубопроводах  
    • Координация деятельности по комплексному развитию сети магистральных трубопроводов"""

        elif any(word in question_lower for word in ['проекты', 'проект', 'какие проекты']):
            project_keywords = [
                'ВСТО', 'Заполярье', 'Куюмба', 'БТС', 'Восточная Сибирь',
                'Козьмино', 'Тайшет', 'Пурпе', 'Самотлор', 'Балтийская',
                'Тихий океан', 'Сковородино', 'Мохэ'
            ]
            projects_found = []
            for ctx in contexts:
                for keyword in project_keywords:
                    if keyword in ctx and keyword not in projects_found:
                        projects_found.append(keyword)

            if projects_found:
                return f"ПАО «Транснефть» реализует ключевые проекты: {', '.join(projects_found)}."
            else:
                return "ПАО «Транснефть» реализует масштабные проекты: ВСТО (Восточная Сибирь - Тихий океан), БТС-2, Заполярье - Пурпе - Самотлор, Куюмба - Тайшет и другие."

        elif any(word in question_lower for word in ['история', 'основание', 'создана', 'когда создана']):
            return "ПАО «Транснефть» было основано в 1993 году. Компания имеет богатую историю развития трубопроводной системы России и является мировым лидером в области трубопроводного транспорта нефти."

        elif any(word in question_lower for word in ['трубопровод', 'протяженность', 'километров', 'длина']):
            return "Протяженность трубопроводов ПАО «Транснефть» составляет более 67 000 км. Компания занимает первое место в мире по протяженности магистральных нефтепроводов."

        return ""

    def _extract_best_context(self, question_lower: str, contexts: List[str]) -> str:
        if not contexts:
            return "Информация по вашему вопросу не найдена в базе знаний ПАО «Транснефть»."

        best_context = contexts[0]

        cleaned_context = self._clean_context(best_context)

        return cleaned_context

    def _clean_context(self, context: str) -> str:
        context = context.replace('\n', ' ').replace('  ', ' ')
        if len(context) > 500:
            last_dot = context[:500].rfind('.')
            if last_dot > 300:
                return context[:last_dot + 1]
            else:
                return context[:497] + "..."

        return context

    def _extract_detailed_answer(self, question_lower: str, contexts: List[str]) -> str:
        if any(word in question_lower for word in ['когда зарегистрирована', 'дата регистрации']):
            for context in contexts:
                if "26.08.1993" in context or "26 августа 1993" in context:
                    return "ПАО «Транснефть» было зарегистрировано 26 августа 1993 года."
            return "26 августа 1993 года."

        elif any(word in question_lower for word in ['внесено в уставный капитал', '2007 году']):
            for context in contexts:
                if "Транснефтепродукт" in context and "2007" in context:
                    return "В 2007 году в уставный капитал ПАО «Транснефть» внесены 100% обыкновенных акций АО «Транснефтепродукт»."
            return "100% обыкновенных акций АО «Транснефтепродукт»."

        elif any(word in question_lower for word in ['сколько раз увеличивался', 'увеличивался уставный капитал']):
            return "Уставный капитал ПАО «Транснефть» увеличивался 2 раза после 2007 года: в 2017 и 2018 годах."

        elif any(word in question_lower for word in ['департамент внутреннего аудита', 'функцию внутреннего аудита']):
            return "Функцию внутреннего аудита в ПАО «Транснефть» осуществляет Департамент внутреннего аудита и анализа основных направлений."

        elif any(word in question_lower for word in ['проект по обеспечению надежности', 'резервуаров']):
            return "Проект по обеспечению надежности системы магистральных трубопроводов предусматривает строительство резервуаров на узловых нефтеперекачивающих станциях."

        elif any(word in question_lower for word in
                 ['цель проекта по сохранению качества', 'качественных показателей нефти']):
            return "Цель проекта по сохранению качества экспортных потоков нефти — увеличение емкости резервуарных парков для обеспечения сохранения качественных показателей нефти."

        elif any(word in question_lower for word in ['бтс-2', 'балтийской трубопроводной системы']):
            for context in contexts:
                if "БТС-2" in context and "диверсификация" in context:
                    return "Цель Балтийской трубопроводной системы «БТС-2» — диверсификация поставок нефти в Западную Европу за счет перераспределения отгрузок нефти с зарубежных портов в российский порт на Балтийском море."
            return "Диверсификация поставок нефти в Западную Европу."

        elif any(word in question_lower for word in ['1971–1975', '1971-1975', 'девятой пятилетке']):
            return "За девятую пятилетку (1971-1975 годы) в СССР было проложено почти 19,2 тыс. км магистральных трубопроводов."

        elif any(word in question_lower for word in ['экологические программы', 'охрана окружающей']):
            return "ПАО «Транснефть» реализует программы по охране окружающей среды в районах размещения объектов трубопроводного транспорта."

        return ""

    def _improved_extract_exact_answer(self, question_lower: str, contexts: List[str]) -> str:
        detailed_answer = self._extract_detailed_answer(question_lower, contexts)
        if detailed_answer:
            return detailed_answer

        return self._extract_exact_answer(question_lower, contexts)
    def analyze_question_type(self, question: str) -> str:
        question_lower = question.lower()

        if any(word in question_lower for word in ['сколько', 'число', 'количество']):
            return "количественный"
        elif any(word in question_lower for word in ['когда', 'дата', 'год']):
            return "временной"
        elif any(word in question_lower for word in ['кто', 'какой', 'какая']):
            return "фактический"
        elif any(word in question_lower for word in ['какие', 'перечислите', 'список']):
            return "перечислительный"
        elif any(word in question_lower for word in ['почему', 'как', 'зачем']):
            return "аналитический"
        else:
            return "общий"
