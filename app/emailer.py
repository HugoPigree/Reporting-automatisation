
from __future__ import annotations
import smtplib, ssl
from email.message import EmailMessage
from pathlib import Path

def _tpl(s: str, **vars) -> str:
    out=s
    for k,v in vars.items(): out=out.replace(f"{{{{{k}}}}}", str(v))
    return out

def send_email(cfg_email: dict, filepath: str, date_str: str):
    if not cfg_email or not cfg_email.get("enabled"):
        return
    smtp_host = cfg_email.get("smtp_host")
    smtp_port = int(cfg_email.get("smtp_port", 587))
    use_tls   = bool(cfg_email.get("use_tls", True))
    username  = cfg_email.get("username")
    password  = cfg_email.get("password")
    from_addr = cfg_email.get("from_addr", username)
    to_addrs  = cfg_email.get("to_addrs", [])
    subject   = _tpl(cfg_email.get("subject", "Rapport {{DATE}}"), DATE=date_str)
    html      = _tpl(cfg_email.get("html", "<p>Voir pièce jointe.</p>"), DATE=date_str)
    if not smtp_host or not to_addrs: raise ValueError("smtp_host ou to_addrs manquants")
    msg=EmailMessage()
    msg["Subject"]=subject; msg["From"]=from_addr; msg["To"]=", ".join(to_addrs)
    msg.set_content("Votre client mail ne supporte pas HTML."); msg.add_alternative(html, subtype="html")
    p=Path(filepath); data=p.read_bytes()
    msg.add_attachment(data, maintype="application", subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=p.name)
    if use_tls:
        ctx=ssl.create_default_context()
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            s.starttls(context=ctx)
            if username and password: s.login(username, password)
            s.send_message(msg)
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as s:
            if username and password: s.login(username, password)
            s.send_message(msg)
