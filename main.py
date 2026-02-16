from fastapi import FastAPI
from fastapi_utils.inferring_router import InferringRouter
from fastapi.middleware.cors import CORSMiddleware
from apis.excel import router as excel_router
from apis.analysis import router as analysis_router
from apis.in_shelf import router as in_shelf_router
from apis.account import router as account_router
import logging
import sys
import os

DEBUG = True
ORIGINS = ['*']

logging.basicConfig(handlers=[logging.FileHandler("logfile.txt", 'w'), logging.StreamHandler(sys.stdout)], level=logging.INFO if bool(os.environ.get('DEBUG', 'False')) else logging.WARNING)

app = FastAPI(root_path='/api/v1')

app.add_middleware(
    CORSMiddleware,
    allow_origins=ORIGINS,
    allow_credentials=True,  # Set to True if you need to support cookies/auth headers
    allow_methods=["*"],     # Allows all standard methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],     # Allows all standard headers
)

app.include_router(excel_router)
app.include_router(analysis_router)
app.include_router(in_shelf_router)
app.include_router(account_router)
