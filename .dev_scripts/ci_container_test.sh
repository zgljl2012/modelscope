pip install -r requirements.txt -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
pip install -r requirements/audio.txt -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
pip install -r requirements/cv.txt -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
pip install -r requirements/multi-modal.txt -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
pip install -r requirements/nlp.txt -f https://modelscope.oss-cn-beijing.aliyuncs.com/releases/repo.html
pip install -r requirements/tests.txt
# install numpy<=1.18 for tensorflow==1.15.x
pip install "numpy<=1.18"

git config --global --add safe.directory /Maas-lib

# linter test
# use internal project for pre-commit due to the network problem
pre-commit run -c .pre-commit-config_local.yaml --all-files
if [ $? -ne 0 ]; then
    echo "linter test failed, please run 'pre-commit run --all-files' to check"
    exit -1
fi
# test with install
python setup.py install

if [ $# -eq 0 ]; then
    ci_command="python tests/run.py --subprocess"
else
    ci_command="$@"
fi
echo "Running case with command: $ci_command"
$ci_command
#python tests/run.py --isolated_cases test_text_to_speech.py test_multi_modal_embedding.py test_ofa_tasks.py test_video_summarization.py
