from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routers import var_covar

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # allow all origins temporarily
    # allow_origins=[
    #     "http://localhost:5173",  # dev server
    #     "https://alfadjalo.github.io",  # your GitHub Pages production URL (no trailing slash)
    # ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(var_covar.router)

@app.get("/")
def root():
    return {"message": "root OK"}

@app.get("/health")
def health_check():
    return {"status": "ok"}
