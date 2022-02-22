FROM lambci/lambda:build-python3.8

WORKDIR /tmp

RUN pip install --upgrade pip
COPY /lambdas/pgstac-loader/requirements.txt requirements.txt
RUN pip install -r requirements.txt -t /asset

RUN find . -type f -name '*.pyc' | while read f; do n=$(echo $f | sed 's/__pycache__\///' | sed 's/.cpython-[2-3][0-9]//'); cp $f $n; done;
RUN find . -type d -a -name '__pycache__' -print0 | xargs -0 rm -rf
RUN find . -type f -a -name '*.py' -print0 | xargs -0 rm -f
RUN find . -type d -a -name 'tests' -print0 | xargs -0 rm -rf
RUN echo "Remove lambda python packages"
RUN rm -rdf ./stack
RUN rm -rdf ./docutils*

COPY /lambdas/pgstac-loader/handler.py handler.py

CMD ["echo", "hello world"]
