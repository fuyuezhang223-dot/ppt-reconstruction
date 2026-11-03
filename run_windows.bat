@echo off
cd /d "%~dp0"
python -m pip install -r requirements.txt
python run_workflow.py build --spec examples/v42_component_demo.json --output outputs/v42_demo.pptx
python -m unittest discover -s tests -p "test_*.py" -v
pause
