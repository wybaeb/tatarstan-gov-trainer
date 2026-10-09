Attribute VB_Name = "TrainingAppeals"
Option Explicit

' Эталон преподавателя для обезличенной учебной выгрузки.
' Код выполняйте только на копии файла.

Public Sub ProcessTrainingAppeals()
    Dim ws As Worksheet, summary As Worksheet, data As Variant, clean() As Variant
    Dim seen As Object, i As Long, j As Long, n As Long, key As String
    Dim registered As Variant, completed As Variant, duration As Variant

    Set ws = ThisWorkbook.Worksheets("Выгрузка")
    data = ws.Range("A1").CurrentRegion.Value2
    ReDim clean(1 To UBound(data, 1), 1 To 11)
    Set seen = CreateObject("Scripting.Dictionary")

    For j = 1 To 9: clean(1, j) = data(1, j): Next j
    clean(1, 10) = "Длительность, дней"
    clean(1, 11) = "Соблюдение срока"
    n = 1

    For i = 2 To UBound(data, 1)
        key = RawRowKey(data, i, 9)
        If Len(Trim$(CStr(data(i, 1)))) > 0 And Not seen.Exists(key) Then
            seen.Add key, True
            n = n + 1
            For j = 1 To 9: clean(n, j) = data(i, j): Next j
            registered = ParseTrainingDate(data(i, 2))
            completed = ParseTrainingDate(data(i, 3))
            clean(n, 2) = registered
            clean(n, 3) = completed
            clean(n, 4) = NormalizeTrainingChannel(data(i, 4))
            If IsDate(registered) And IsDate(completed) Then
                duration = CLng(completed) - CLng(registered)
                clean(n, 10) = duration
                clean(n, 11) = IIf(duration <= CLng(data(i, 7)), 1, 0)
            Else
                clean(n, 10) = Empty
                clean(n, 11) = 0
            End If
        End If
    Next i

    Application.ScreenUpdating = False
    ws.Cells.ClearContents
    ws.Range("A1").Resize(n, 11).Value2 = clean
    ws.Columns(2).NumberFormat = "dd.mm.yyyy"
    ws.Columns(3).NumberFormat = "dd.mm.yyyy"
    ws.Columns.AutoFit

    On Error Resume Next
    Application.DisplayAlerts = False
    ThisWorkbook.Worksheets("Сводка").Delete
    Application.DisplayAlerts = True
    On Error GoTo 0
    Set summary = ThisWorkbook.Worksheets.Add(After:=ws)
    summary.Name = "Сводка"

    Dim lastChannel As Long
    lastChannel = WriteTrainingSummary(summary, clean, n, 4, 1, "Канал")
    Call WriteTrainingSummary(summary, clean, n, 5, lastChannel + 3, "Категория")

    Dim chart As ChartObject
    Set chart = summary.ChartObjects.Add(Left:=430, Top:=20, Width:=470, Height:=280)
    chart.Chart.ChartType = xlColumnClustered
    chart.Chart.SetSourceData summary.Range("A1:A" & lastChannel & ",D1:D" & lastChannel)
    chart.Chart.HasTitle = True
    chart.Chart.ChartTitle.Text = "Доля завершённых в срок по каналам"
    Application.ScreenUpdating = True
End Sub

Private Function RawRowKey(ByRef data As Variant, ByVal rowNumber As Long, ByVal lastColumn As Long) As String
    Dim j As Long, part As String
    For j = 1 To lastColumn
        part = part & Len(CStr(data(rowNumber, j))) & ":" & CStr(data(rowNumber, j)) & "|"
    Next j
    RawRowKey = part
End Function

Private Function ParseTrainingDate(ByVal value As Variant) As Variant
    Dim s As String, p As Variant
    s = Trim$(CStr(value))
    If Len(s) = 0 Or LCase$(s) = "н/д" Then ParseTrainingDate = Empty: Exit Function
    If InStr(s, ".") > 0 Then
        p = Split(s, ".")
        If UBound(p) = 2 Then ParseTrainingDate = DateSerial(CLng(p(2)), CLng(p(1)), CLng(p(0))): Exit Function
    ElseIf InStr(s, "-") > 0 Then
        p = Split(s, "-")
        If UBound(p) = 2 Then ParseTrainingDate = DateSerial(CLng(p(0)), CLng(p(1)), CLng(p(2))): Exit Function
    End If
    ParseTrainingDate = Empty
End Function

Private Function NormalizeTrainingChannel(ByVal value As Variant) As String
    Dim s As String
    s = LCase$(Trim$(Replace(CStr(value), "ё", "е")))
    If InStr(s, "портал") > 0 Then
        NormalizeTrainingChannel = "Портал"
    ElseIf s = "кц" Or InStr(s, "контакт") > 0 Or InStr(s, "горяч") > 0 Then
        NormalizeTrainingChannel = "Контакт-центр"
    ElseIf InStr(s, "пись") > 0 Or InStr(s, "почт") > 0 Then
        NormalizeTrainingChannel = "Письменное обращение"
    ElseIf InStr(s, "прием") > 0 Or InStr(s, "очн") > 0 Then
        NormalizeTrainingChannel = "Личный приём"
    Else
        NormalizeTrainingChannel = "Требуется уточнение"
    End If
End Function

Private Function WriteTrainingSummary(ByVal ws As Worksheet, ByRef data As Variant, ByVal n As Long, _
                                      ByVal groupColumn As Long, ByVal startRow As Long, ByVal title As String) As Long
    Dim total As Object, completed As Object, onTime As Object, i As Long, r As Long, k As String, item As Variant
    Set total = CreateObject("Scripting.Dictionary")
    Set completed = CreateObject("Scripting.Dictionary")
    Set onTime = CreateObject("Scripting.Dictionary")
    For i = 2 To n
        k = CStr(data(i, groupColumn))
        If Not total.Exists(k) Then total.Add k, 0: completed.Add k, 0: onTime.Add k, 0
        total(k) = total(k) + 1
        If LCase$(CStr(data(i, 6))) = "завершено" Then completed(k) = completed(k) + 1
        onTime(k) = onTime(k) + CLng(data(i, 11))
    Next i
    ws.Cells(startRow, 1).Resize(1, 4).Value = Array(title, "Обращений", "Завершено", "Доля в срок")
    r = startRow
    For Each item In total.Keys
        r = r + 1
        ws.Cells(r, 1).Resize(1, 4).Value = Array(item, total(item), completed(item), onTime(item) / total(item))
    Next item
    ws.Range(ws.Cells(startRow + 1, 4), ws.Cells(r, 4)).NumberFormat = "0.0%"
    WriteTrainingSummary = r
End Function
