Class dc.python.HelloWorld Extends %RegisteredObject
{

/// Call a custom Python module
ClassMethod CallSay()
{
    Set mylib = ##class(%SYS.Python).Import("irisapp.helloworld")
    Do mylib.say()
}

ClassMethod Teste()
{
    Set sql = ""_
    "WITH CustomerTotals AS (" _
    "  SELECT Customer, SUM(Amount) Total" _
    "  FROM DemoCTE.DemoOrders" _
    "  GROUP BY Customer" _
    ") " _
    "SELECT * FROM CustomerTotals"
    Set stmt = ##class(%SQL.Statement).%New()
    $$$ThrowOnError(stmt.%Prepare(sql))
    Set result = stmt.%Execute()
    If (result.%SQLCODE '= 0) && (result.%SQLCODE '= 100) {
        Throw ##class(%Exception.SQL).CreateFromSQLCODE(result.%SQLCODE, result.%Message)
    }
    While result.%Next() {
        Write result.Customer, " ", result.Total, !
    }
}

}
