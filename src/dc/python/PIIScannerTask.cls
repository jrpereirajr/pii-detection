Class dc.python.PIIScannerTask Extends %SYS.Task.Definition
{

Parameter TaskName = "PII Scanner Python Task";

Property OutputPath As %String [ InitialExpression = "/home/irisowner/dev/pii_report.csv" ];

Property SampleSize As %Integer [ InitialExpression = 100 ];

Method OnTask() As %Status
{
	Set sc = $$$OK
	Try {
		Set sys = ##class(%SYS.Python).Import("sys")
		Do sys.path.insert(0, "/usr/irissys/lib/python")
		If sys.modules."__contains__"("iris") {
			Do sys.modules.pop("iris")
		}
		Set piiModule = ##class(%SYS.Python).Import("irisapp.pii_discovery.__main__")
		Set ns = $Namespace
		Do piiModule.run(..OutputPath, ..SampleSize, ns)
	}
	Catch ex {
		Set sc = ex.AsStatus()
		Do ##class(%SYS.System).WriteToConsoleLog("PII Scanner Task error: "_ex.DisplayString())
	}
	Quit sc
}

ClassMethod RegisterTask() As %Status
{
	Set sc = $$$OK
	Try {
		Set taskName = "PII Scanner Python Task"
		New $Namespace
		Set $Namespace = "%SYS"
		Set rs = ##class(%SQL.Statement).%ExecDirect(,"SELECT ID FROM %SYS.Task WHERE Name = ?",taskName)
		If rs.%Next() {
			Set sc = $$$OK
		} Else {
			Set task = ##class(%SYS.Task).%New()
			Set task.Name = taskName
			Set task.Description = "Runs PII Discovery scan and generates CSV report"
			Set task.NameSpace = "IRISAPP"
			Set task.TaskClass = "dc.python.PIIScannerTask"
			Set task.TimePeriod = 0
			Set task.TimePeriodEvery = 1
			Set task.DailyFrequency = 0
			Set task.DailyStartTime = 7200
			Set sc = task.%Save()
			If $$$ISOK(sc) {
				Do ##class(%SYS.Task).Resume(task.%Id())
			}
		}
	}
	Catch ex {
		Set sc = ex.AsStatus()
		Do ##class(%SYS.System).WriteToConsoleLog("PII Scanner Task registration error: "_ex.DisplayString())
	}
	Quit sc
}

}
