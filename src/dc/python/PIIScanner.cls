Class dc.python.PIIScanner Extends %RegisteredObject
{

/// Call the Python module for PII scanning with default args
ClassMethod CallPIIScanner()
{
	Set sys = ##class(%SYS.Python).Import("sys")
	Do sys.path.insert(0, "/usr/irissys/lib/python")
	If sys.modules."__contains__"("iris") {
		Do sys.modules.pop("iris")
	}
	Set piiScanner = ##class(%SYS.Python).Import("irisapp.pii_discovery.__main__")
	Do piiScanner.run()
}

/// Call the Python module for PII scanning with custom args
ClassMethod CallPIIScannerWithArgs(outputPath As %String, sampleSize As %Integer, namespace As %String)
{
	Set sys = ##class(%SYS.Python).Import("sys")
	Do sys.path.insert(0, "/usr/irissys/lib/python")
	If sys.modules."__contains__"("iris") {
		Do sys.modules.pop("iris")
	}
	Set piiScanner = ##class(%SYS.Python).Import("irisapp.pii_discovery.__main__")
	Do piiScanner.run(outputPath, sampleSize, namespace)
}

ClassMethod Teste() [ Language = python ]
{
	import sys
	import importlib

	iris_official_path = '/usr/irissys/lib/python'
	sys.path.insert(0, iris_official_path)

	if 'iris' in sys.modules:
		del sys.modules['iris']

	import iris

	print(f"Módulo iris carregado de: {iris.__file__}")

	print(iris.system.Process.NameSpace())
}

}
