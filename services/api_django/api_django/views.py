from django.http import JsonResponse

def healthz(request):
    return JsonResponse({"status": "ok"})

def metrics(request):
    return JsonResponse({"uptime": "TBD", "requests": "TBD"})
