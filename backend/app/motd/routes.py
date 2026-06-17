"""Routes du MOTD : template, aperçu live, balises disponibles."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from ..core import store
from ..vms import repository
from .render import available_tags, render

router = APIRouter(prefix="/api/motd", tags=["motd"])


class PreviewRequest(BaseModel):
    template: str
    vm_id: str | None = None


@router.get("/template")
def get_template() -> dict:
    s = store.read_settings()
    return {"template": s["motd_template"], "lab_name": s["lab_name"], "lab_line": s["lab_line"]}


@router.put("/template")
def save_template(body: dict) -> dict:
    s = store.read_settings()
    s["motd_template"] = body.get("template", s["motd_template"])
    store.write_settings(s)
    return {"ok": True}


@router.post("/preview")
def preview(req: PreviewRequest) -> dict:
    s = store.read_settings()
    vm = repository.get_vm(req.vm_id) if req.vm_id else _first_vm()
    if vm is None:
        warning = "Aucune VM enregistrée — balises non remplacées"
        return {"rendered": req.template, "tags": available_tags(None), "warning": warning}
    rendered = render(req.template, vm, s["lab_name"], s["lab_line"])
    return {"rendered": rendered, "tags": available_tags(vm), "vm_name": vm.name}


def _first_vm():
    vms = repository.list_vms()
    return vms[0] if vms else None
