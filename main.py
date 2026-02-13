from fastapi import FastAPI
from fastapi_utils.inferring_router import InferringRouter
from apis.excel import router as excel_router
from apis.analysis import router as analysis_router
import logging
import sys
import os

DEBUG = True
logging.basicConfig(handlers=[logging.FileHandler("logfile.txt", 'w'), logging.StreamHandler(sys.stdout)], level=logging.INFO if bool(os.environ.get('DEBUG', 'False')) else logging.WARNING)

app = FastAPI(root_path='/api/v1')
app.include_router(excel_router)
app.include_router(analysis_router)
