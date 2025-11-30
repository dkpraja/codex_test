from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML_FILE = ROOT / "index.html"


class TagCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.sections = {}
        self.forms = []
        self.stylesheets = []

    def handle_starttag(self, tag, attrs):
        attr_dict = dict(attrs)
        if tag == "a" and "href" in attr_dict:
            self.links.append(attr_dict["href"])
        if tag in {"section", "div"} and "id" in attr_dict:
            self.sections[attr_dict["id"]] = True
        if tag == "form":
            self.forms.append(attr_dict)
        if tag == "link" and attr_dict.get("rel") == "stylesheet":
            href = attr_dict.get("href")
            if href:
                self.stylesheets.append(href)
        if tag == "input" or tag == "textarea":
            if self.forms:
                current_form = self.forms[-1]
                inputs = current_form.setdefault("inputs", [])
                inputs.append((tag, attr_dict))


def parse_html():
    parser = TagCollector()
    parser.feed(HTML_FILE.read_text(encoding="utf-8"))
    return parser


def test_nav_links_present():
    parser = parse_html()
    expected = {"#collections", "#custom", "#process", "#contact"}
    assert expected.issubset(set(parser.links)), "Navigation should link to all key sections"


def test_sections_exist():
    parser = parse_html()
    required_sections = {"collections", "custom", "process", "contact"}
    missing = required_sections - parser.sections.keys()
    assert not missing, f"Missing section(s): {', '.join(sorted(missing))}"


def test_contact_form_fields_and_required_attributes():
    parser = parse_html()
    assert parser.forms, "Contact form should be present"
    form = parser.forms[-1]
    inputs = form.get("inputs", [])
    attrs = {name: attr for tag, attr_dict in inputs if (name := attr_dict.get("name")) for attr in [attr_dict]}

    name_field = attrs.get("name")
    email_field = attrs.get("email")
    textarea_field = next((attr_dict for tag, attr_dict in inputs if tag == "textarea" and attr_dict.get("name") == "details"), None)

    assert name_field and "required" in name_field, "Name input should be required"
    assert email_field and email_field.get("type") == "email" and "required" in email_field, (
        "Email input should be required and use email type"
    )
    assert textarea_field is not None, "Toy idea textarea should be present"


def test_css_file_is_linked():
    parser = parse_html()
    assert "styles.css" in parser.stylesheets, "styles.css should be linked in the head"
