FROM blockchain_bi_base    

ENV TZ Asia/Shanghai       

ADD . /home    

VOLUME [ "/home/log" ]     
WORKDIR /home

EXPOSE 1922

CMD ["python", "app.py"]