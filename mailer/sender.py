"""Send formatted digest newsletters via SMTP."""

import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Dict, Any
from datetime import datetime

from config import EmailConfig


logger = logging.getLogger(__name__)


class EmailSender:
    def __init__(self, config: EmailConfig):
        self.config = config
        
    def send_digest(self, items: List[Dict[str, Any]]) -> bool:
        try:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Monthly AI & ML Digest – {datetime.now().strftime('%B %Y')}"
            message["From"] = self.config.sender_email
            message["To"] = self.config.recipient_email
            message.attach(MIMEText(self._create_html_body(items), "html"))
            self._send_email(message)
            return True
        except Exception as e:
            logger.error(f"Failed to send digest: {e}")
            return False
            
    def _create_html_body(self, items: List[Dict[str, Any]]) -> str:
        month_year = datetime.now().strftime("%B %Y")
        html = f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><style>
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;line-height:1.6;color:#333;max-width:700px;margin:0 auto;padding:20px;background:#f5f5f5}}
.container{{background:#fff;border-radius:8px;padding:40px;box-shadow:0 2px 4px rgba(0,0,0,0.1)}}
h1{{color:#1a73e8;border-bottom:3px solid #1a73e8;padding-bottom:10px}}
.item{{margin-bottom:30px;padding-bottom:20px;border-bottom:1px solid #e0e0e0}}
.category{{display:inline-block;padding:4px 12px;border-radius:4px;font-size:12px;font-weight:600;margin-bottom:8px}}
.category-research{{background:#e8f0fe;color:#1967d2}}.category-tooling{{background:#e6f4ea;color:#137333}}
.category-industry{{background:#fef7e0;color:#e37400}}.category-funding{{background:#fce8e6;color:#c5221f}}
.why-matters{{background:#f8f9fa;padding:12px;border-left:4px solid #1a73e8;margin:12px 0;font-style:italic}}
</style></head><body><div class="container"><h1>AI & ML Digest</h1><p>{month_year}</p>"""
        for item in items:
            cat = item.get("category", "Industry")
            html += f'<div class="item"><span class="category category-{cat.lower()}">{cat}</span><h2>{item.get("title","")}</h2><p>{item.get("summary","")}</p><div class="why-matters"><strong>Why it matters:</strong> {item.get("why_it_matters","")}</div><a href="{item.get("url","#")}">Read more →</a></div>'
        html += '<div style="margin-top:40px;text-align:center;color:#666;font-size:13px"><p>Monthly AI/ML Digest – Auto-curated</p></div></div></body></html>'
        return html
        
    def _send_email(self, message: MIMEMultipart) -> None:
        if self.config.use_tls:
            server = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
            server.starttls()
        else:
            server = smtplib.SMTP_SSL(self.config.smtp_host, self.config.smtp_port)
        server.login(self.config.sender_email, self.config.sender_password)
        server.send_message(message)
        server.quit()
