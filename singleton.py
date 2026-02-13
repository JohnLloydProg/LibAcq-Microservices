from services import ExcelService, AnalysisService

excel_service_singleton:ExcelService = None
analysis_service_singleton:AnalysisService = None

def get_excel_service() -> ExcelService:
    global excel_service_singleton
    if not excel_service_singleton:
        excel_service_singleton = ExcelService()
    return excel_service_singleton

analysis_service_singleton:ExcelService = None

def get_analysis_service() -> AnalysisService:
    global excel_service_singleton
    if not excel_service_singleton:
        excel_service_singleton = AnalysisService()
    return excel_service_singleton