import os
import subprocess
import logging

from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)
app = FastAPI()

# Ensure the data directory exists
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)


@app.get("/")
async def read_index():
    return FileResponse("www/index.html")


@app.post("/print")
async def print_markdown(markdown: str = Form(...)):
    # Save markdown text to a file
    temp_file_path = os.path.join(DATA_DIR, "print_job.md")

    try:
        with open(temp_file_path, "w") as f:
            f.write(markdown)
    except Exception as e:
        logger.exception("Failed to save print job to %s", temp_file_path)
        raise HTTPException(status_code=500,
                            detail=f"Failed to save file: {str(e)}")

    # Execute print.py with the file as a parameter
    try:
        # We use sys.executable to ensure we use the same python environment
        import sys
        logger.info("Executing print script for %s", temp_file_path)
        result = subprocess.run(
            [sys.executable, "print.py", temp_file_path],
            capture_output=True,
            text=True,
            env=os.environ.copy()
        )

        if result.returncode != 0:
            logger.error("Print script failed with code %s. stdout=%r stderr=%r",
                         result.returncode,
                         result.stdout,
                         result.stderr)
            error_msg = f"STDOUT: {result.stdout}\nSTDERR: {result.stderr}"
            raise HTTPException(status_code=500,
                                detail=f"Print script error:\n{error_msg}")

        return {"status": "success", "message": "Printed successfully"}
    except Exception as e:
        logger.exception("Failed to execute print script for %s",
                         temp_file_path)
        raise HTTPException(status_code=500,
                            detail=f"Failed to execute print script: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
