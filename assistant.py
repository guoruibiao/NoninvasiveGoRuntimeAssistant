# coding: utf8
import os
import sys


def trim(raw, subset=[]):
    for char in subset:
        raw = str(raw).strip(char)
    for char in subset[::-1]:
        raw = str(raw).strip(char)
    return raw


def has_keywords(line):
    # 特意加了空格，因为部分变量可能会出问题
    keywords = [
        "if ", "for ", "func ", "import ", "package ", "type ", "defer ", "go ", "goto ", "var ", "fmt.",
        "return ", "const ", "switch ", "else ", "//", "// ", "/*", "/**", "/* ", "/** ", "{", "}"
    ]
    subset = ["", "\t", "\n", " ", ":", "_", ","]
    line = trim(line, subset)
    for keyword in keywords:
        if line.startswith(keyword):
            return True
    return False


class Engine(object):

    def __init__(self):
        self.lines = None

    def readLines(self, filename):
        with open(filename, "r") as f:
            self.lines = f.readlines()
            f.close()

    def writeLines(self, filename):
        with open(filename, "w") as f:
            f.writelines(self.lines)
            f.close()

    def _handleImport(self):
        retMap = {
            "fmt": False,
            "runtime": False,
            "packageline": 0,
            "package": ""
        }
        counter = 0
        for line in self.lines:
            oldline = line
            line = trim(line, ["\t", " ", "", "\n"])
            if line == '"fmt"':
                retMap["fmt"] = True
            elif line == '"runtime"':
                retMap["runtime"] = True
            # 记录 package 所在行数
            if line.startswith("package"):
                retMap["packageline"] = counter
                retMap["package"] = oldline
            counter += 1
        # 针对特殊引入情况进行 import 补充
        result = []
        del self.lines[retMap["packageline"]]
        if retMap["fmt"] == False and retMap["runtime"] == False:
            result.append(retMap["package"])
            result.extend(self.lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "fmt"\n')
            result.append('    "runtime"\n')
            result.append(")\n")
            result.extend(self.lines[retMap["packageline"]:])
        elif retMap["fmt"] == True and retMap["runtime"] == False:
            result.append(retMap["package"])
            result.extend(self.lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "runtime"\n')
            result.append(")\n")
            result.extend(self.lines[retMap["packageline"]:])
        elif retMap["fmt"] == False and retMap["runtime"] == True:
            result.append(retMap["package"])
            result.extend(self.lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "fmt"\n')
            result.append(")\n")
            result.extend(self.lines[retMap["packageline"]:])
        else:
            result = self.lines
        print(result)
        self.lines = result

    def _shouldPadding(self, line):
        """
            Go 的正常赋值语句基本上也就那几种，考虑好前缀为"_"的特殊情况即可
            =
            :=
            """
        subset = ["", "\t", "\n", " ", ":", "_", ","]
        line = trim(line, subset)
        if line == "":
            return False, ""

        if "=" not in line:
            return False, ""

        if has_keywords(line):
            return False, ""

        if "==" in line:
            return False, ""

        # 处理 = 以及 := 的case
        row = line.split("=")
        if len(row) <= 0:
            return False, ""

        # 处理类似于 waitGroup := &sync.WaitGroup{}
        for ends in ["&", "{", "+="]:
            if trim(ends, [" ", "", "\t"]).startswith(ends):
                return False, ""

        # 处理 log.Warn("abc=%s")
        if r'"' in str(row[0]) or r'`' in str(row[0]) or r'%' in str(row[0]):
            return False, ""

        prefix, variables = row[0], []
        if "," in prefix:
            variables = [trim(variable, subset=subset) for variable in prefix.split(",")]
        else:
            variables = [trim(prefix, subset=[" ", ":"])]
        if len(variables) <= 0:
            return False, ""

        # print("variables=", variables)
        # print("prefix=", prefix)
        tmp = []
        for variable in variables:
            variable = trim(variable, [" ", "\t"])
            if variable == "_" or variable == "":
                continue
            tmp.append(variable)
        variables = tmp

        result = ""
        for variable in variables:
            result += "{}=%v ".format(variable)

        if result == "":
            return False, ""

        parameters = ", ".join(variables)
        template = """
                defer func() {{
                    pc, file, line, _ := runtime.Caller(0)
                    fmt.Printf("DEBUG_PADDING Name=%s, file=%s, line=%d {} ", runtime.FuncForPC(pc).Name(), file, line, {})
                    fmt.Println()
                }}()
            """
        result = template.format(result, parameters)
        # print(result)
        return True, result

    def handle(self, filename):
        self.readLines(filename)
        # 如果一行也没替换 则不进行 import 处理
        hasFunc, funcStartLine = False, -1
        for line in self.lines:
            funcStartLine += 1
            if trim(line, [" ", "\t"]).startswith("func "):
                hasFunc = True
                break
        # 无需进行 defer 处理，直接退出
        if not hasFunc:
            return

        # 记录最终 lines
        result = self.lines[:funcStartLine]
        # 处理 func 内的 defer 问题
        everPadded = False
        for line in self.lines[funcStartLine:]:
            result.append(line)
            should, newLine = self._shouldPadding(line)
            if should:
                everPadded = True
                result.append(newLine)
        self.lines = result
        # 最后处理 package 和 import 问题
        if everPadded:
            self._handleImport()

        # 文件写回
        # print(self.lines)
        filename = "/tmp/demo.go"
        self.writeLines(filename)
        print("{} done.".format(filename))

def walk(source):
    filenames = []
    for fpathe, dirs, fs in os.walk(source):
        for f in fs:
            filename = os.path.join(fpathe, f)
            if filename.endswith(".go") and not filename.endswith("_test.go"):
                filenames.append(filename)
    return filenames

if __name__ == "__main__":
    engine = Engine()
    filename = "/tmp/activity/models/logic/activity_goods.go"
    engine.handle(filename)

    # handlePath = "/tmp/activity/models/logic/"
    """
    handlePath = sys.argv[1]
    if handlePath == "":
        print("handle path empty")
        sys.exit(0)

    filenames = walk(handlePath)
    engine = Engine()
    for filename in filenames:
        engine.lines = []
        engine.handle(filename)
    print("path: {} all done.")
    """