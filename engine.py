# coding:utf8
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
        "return ", "const "
    ]
    subset = ["", "\t", "\n", " ", ":", "_", ","]
    line = trim(line, subset)
    for keyword in keywords:
        if line.startswith(keyword):
            return True
    return False


def should_padding(line):
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

    # const 常量问题处理
    if type(row[1]) in [int, str]:
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
    result = ""
    for variable in variables:
        result += "{}=%v ".format(variable)

    if result == "":
        return False, ""

    parameters = ", ".join(variables)
    template = """
        defer func() {{
            pc, file, line, _ := runtime.Caller(0)
            fmt.Printf("Name=%s, file=%s, line=%d {}", runtime.FuncForPC(pc).Name(), file, line, {})
        }}()
    """
    result = template.format(result, parameters)
    # print(result)
    return True, result



def should_padding_test():
    testcases = [
        "pc, file, line ,ok := runtime.Caller(0)",
        'ret := fmt.Sprintf("f", frsrcid)',
        "fui := fmtUserInfo{"
    ]
    for testcase in testcases:
        print(should_padding(testcase))

def handle_import(filename):
    with open(filename, "r") as fread:
        lines = fread.readlines()
        fread.close()
        retMap = {
            "fmt": False,
            "runtime": False,
            "packageline": 0,
            "package": ""
        }
        counter = 0
        for line in lines:
            line = trim(line, ["\t", " ", ""])
            if line == '"fmt"':
                retMap["fmt"] = True
            elif line == '"runtime"':
                retMap["runtime"] = True
            # 记录 package 所在行数
            if "package" in line:
                retMap["packageline"] = counter
                retMap["package"] = line
            counter += 1
        # 针对特殊引入情况进行 import 补充
        result = []
        del lines[retMap["packageline"]]
        if retMap["fmt"] == False and retMap["runtime"] == False:
            result.append(retMap["package"])
            result.extend(lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "fmt"\n')
            result.append('    "runtime"\n')
            result.append(")\n")
            result.extend(lines[retMap["packageline"]:])
        elif retMap["fmt"] == True and retMap["runtime"] == False:
            result.append(retMap["package"])
            result.extend(lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "runtime"\n')
            result.append(")\n")
            result.extend(lines[retMap["packageline"]:])
        elif retMap["fmt"] == False and retMap["runtime"] == True:
            result.append(retMap["package"])
            result.extend(lines[:retMap["packageline"]])
            result.append("import (\n")
            result.append('    "fmt"\n')
            result.append(")\n")
            result.extend(lines[retMap["packageline"]:])
        else:
            result = lines
        # print(result)

        # 写回文件
        with open(filename, "w") as fwrite:
            fwrite.writelines(result)
            fwrite.close()


def rewrite_file(filename, outputname):
    with open(filename, "r") as fread:
        lines = fread.readlines()
        fread.close()
    result = []
    for line in lines:
        should, anotherline = should_padding(line)
        result.append(line)
        if should == True:
            result.append(anotherline)
    # 写回文件
    with open(outputname, "w") as fwrite:
        fwrite.writelines(result)
        fwrite.close()
    print("{} done.".format(filename))
    # import handle
    handle_import(filename)



def walk(source):
    for fpathe, dirs, fs in os.walk(source):
        for f in fs:
            filename = os.path.join(fpathe, f)
            if filename.endswith(".go") and not filename.endswith("_test.go"):
                rewrite_file(filename, filename)
                print("{} rewrite done.".format(filename))


if __name__ == "__main__":
    # should_padding_test()
    # filename = "/Users/guoruibiao/PycharmProjects/NoninvasiveGoRuntimeAssistant/workdir/method-self.go"
    # outputname = "/Users/guoruibiao/PycharmProjects/NoninvasiveGoRuntimeAssistant/workdir/method-self.go"
    # filename = sys.argv[1]
    # outputname = sys.argv[2]
    # rewrite_file(filename, outputname)

    walk(sys.argv[1])