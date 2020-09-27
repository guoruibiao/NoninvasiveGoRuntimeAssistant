#!/usr/bin/env bash

CUR_DIR=`PWD`
WORKDIR=$CUR_DIR/workdir
SOURCE_CODE=/Users/guoruibiao/go/src/sunflower/

rm -rf "$WORKDIR"
echo "已删除 $WORKDIR 目录"
ls
# 不存在工作区则进行创建
if [ ! -d "$WORKDIR" ]; then
  mkdir "$WORKDIR"
fi

cp -r $SOURCE_CODE $WORKDIR
cd "$WORKDIR"/activity || exit
if [ ! -f "$WORKDIR/go.mod" ]; then
  go mod init github.com/guoruibiao/noninvasivegoruntimeassistant
fi

# 开始添加侵入式代码
python ../engine.py "$WORKDIR"

# 执行入口函数
ls
go run main.go

