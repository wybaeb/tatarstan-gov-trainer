Attribute VB_Name = "TrainingRolling30"
Option Explicit
Public Sub BuildRolling30()
    Dim oldScreen As Boolean, oldEvents As Boolean, oldCalc As XlCalculation
    Dim wb As Workbook, src As Worksheet, daily As Worksheet, monthly As Worksheet
    Dim a As Variant, outDay(1 To 365, 1 To 5) As Variant, outMonth(1 To 12, 1 To 3) As Variant
    Dim counts() As Double, prefix() As Double, ids As Object
    Dim firstDate As Long, lastDate As Long, startReport As Long, lastRow As Long
    Dim i As Long, k As Long, ix As Long, m As Long, n As Long, dt As Long, dayCount As Long
    Dim rolling As Double, totalMonth(1 To 12) As Double, daysMonth(1 To 12) As Long
    Dim ch As ChartObject, errText As String, key As String
    oldScreen = Application.ScreenUpdating: oldEvents = Application.EnableEvents: oldCalc = Application.Calculation
    On Error GoTo Failed
    Set wb = ThisWorkbook: Set src = wb.Worksheets("Обращения")
    Set daily = wb.Worksheets("Окно 30 дней"): Set monthly = wb.Worksheets("Итог окна")
    firstDate = CLng(DateSerial(2024, 12, 1)): lastDate = CLng(DateSerial(2025, 12, 31))
    startReport = CLng(DateSerial(2025, 1, 1)): n = lastDate - firstDate + 1
    ReDim counts(1 To n): ReDim prefix(0 To n)
    lastRow = src.Cells(src.Rows.Count, 1).End(xlUp).Row
    a = src.Range("A2:D" & lastRow).Value2
    Set ids = CreateObject("Scripting.Dictionary")
    For i = 1 To UBound(a, 1)
        key = Trim$(CStr(a(i, 1)))
        If Len(key) = 0 Or ids.Exists(key) Then Err.Raise 5, , "Пустой или повторный ID, строка " & i + 1
        ids.Add key, True
        If Not IsNumeric(a(i, 2)) Then Err.Raise 5, , "Дата не является датой Excel, строка " & i + 1
        If CDbl(a(i, 2)) <> Fix(CDbl(a(i, 2))) Then Err.Raise 5, , "Дата содержит время, строка " & i + 1
        dt = CLng(a(i, 2))
        If dt < firstDate Or dt > lastDate Then Err.Raise 5, , "Дата вне учебного периода, строка " & i + 1
        counts(dt - firstDate + 1) = counts(dt - firstDate + 1) + 1
    Next i
    For i = 1 To n
        prefix(i) = prefix(i - 1) + counts(i)
    Next i
    k = 0
    For dt = startReport To lastDate
        k = k + 1: ix = dt - firstDate + 1
        rolling = prefix(ix) - prefix(ix - 30)
        outDay(k, 1) = dt: outDay(k, 2) = counts(ix): outDay(k, 3) = rolling
        outDay(k, 4) = rolling / 30#: outDay(k, 5) = outDay(k, 4) * 30#
        m = Month(CDate(dt)): totalMonth(m) = totalMonth(m) + outDay(k, 5): daysMonth(m) = daysMonth(m) + 1
    Next dt
    For m = 1 To 12
        outMonth(m, 1) = CLng(DateSerial(2025, m, 1))
        outMonth(m, 2) = totalMonth(m) / daysMonth(m): outMonth(m, 3) = outMonth(m, 2) / 30#
    Next m
    Application.ScreenUpdating = False: Application.EnableEvents = False: Application.Calculation = xlCalculationManual
    daily.Range("A2:E366").Value2 = outDay: monthly.Range("A2:C13").Value2 = outMonth
    daily.Range("A2:A366").NumberFormat = "dd.mm.yyyy": monthly.Range("A2:A13").NumberFormat = "mmm yyyy"
    daily.Range("C2:E366").NumberFormat = "0.00": monthly.Range("B2:C13").NumberFormat = "0.00"
    On Error Resume Next
    Set ch = monthly.ChartObjects("Rolling30")
    On Error GoTo Failed
    If ch Is Nothing Then
        Set ch = monthly.ChartObjects.Add(360, 20, 620, 350): ch.Name = "Rolling30"
    End If
    With ch.Chart
        .ChartType = xlLineMarkers: .SetSourceData Source:=monthly.Range("A1:B13")
        .HasTitle = True: .ChartTitle.Text = "Средний 30-дневный индекс по месяцам"
        .HasLegend = False
    End With
    GoTo Restore
Failed:
    errText = Err.Description
Restore:
    Application.ScreenUpdating = oldScreen: Application.EnableEvents = oldEvents: Application.Calculation = oldCalc
    If Len(errText) > 0 Then MsgBox errText, vbExclamation Else MsgBox "Расчёт готов. Сверьте лист Контроль.", vbInformation
End Sub
