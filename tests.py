#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import logging
from io import StringIO

import cssutils
import mock

import pynliner
from pynliner import Pynliner

unicode = getattr(__builtins__, 'unicode', str)


class Basic(unittest.TestCase):
    def setUp(self):
        self.html = "<style>h1 { color:#ffcc00; }</style><h1>Hello World!</h1>"
        self.p = Pynliner().from_string(self.html)

    def test_fromString(self):
        """Test 'fromString' constructor"""
        self.assertEqual(self.p.source_string, self.html)

    def test_get_soup(self):
        """Test '_get_soup' method"""
        self.p._get_soup()
        self.assertEqual(unicode(self.p.soup), self.html)

    def test_get_styles(self):
        """Test '_get_styles' method"""
        self.p._get_soup()
        self.p._get_styles()
        self.assertEqual(self.p.style_string, u'h1 { color:#ffcc00; }\n')
        self.assertEqual(unicode(self.p.soup), u'<h1>Hello World!</h1>')

    def test_apply_styles(self):
        """Test '_apply_styles' method"""
        self.p._get_soup()
        self.p._get_styles()
        self.p._apply_styles()
        attr_dict = dict(self.p.soup.contents[0].attrs)
        self.assertTrue('style' in attr_dict)
        self.assertEqual(attr_dict['style'], u'color: #fc0')

    def test_run(self):
        """Test 'run' method"""
        output = self.p.run()
        self.assertEqual(output, u'<h1 style="color: #fc0">Hello World!</h1>')

    def test_with_cssString(self):
        """Test 'with_cssString' method"""
        cssString = 'h1 {color: #f00;}'
        self.p.with_cssString(cssString)
        output = self.p.run()
        self.assertEqual(output, u'<h1 style="color: #f00">Hello World!</h1>')

    def test_fromString_complete(self):
        """Test 'fromString' complete"""
        output = pynliner.fromString(self.html)
        desired = u'<h1 style="color: #fc0">Hello World!</h1>'
        self.assertEqual(output, desired)

    def test_fromURL(self):
        """Test 'fromURL' constructor"""
        url = 'http://media.tannern.com/pynliner/test.html'
        p = Pynliner()
        with mock.patch.object(Pynliner, '_get_url') as mocked:
            mocked.return_value = u"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>test</title>
<link rel="stylesheet" type="text/css" href="test.css"/>
<style type="text/css">h1 {color: #fc0;}</style>
</head>
<body>
<h1>Hello World!</h1>
<p>:)</p>
</body>
</html>"""
            p.from_url(url)
        self.assertEqual(p.root_url, 'http://media.tannern.com')
        self.assertEqual(p.relative_url, 'http://media.tannern.com/pynliner/')

        p._get_soup()

        with mock.patch.object(Pynliner, '_get_url') as mocked:
            mocked.return_value = 'p {color: #999}'
            p._get_external_styles()
        self.assertEqual(p.style_string, "p {color: #999}")

        p._get_internal_styles()
        self.assertEqual(p.style_string, "p {color: #999}\nh1 {color: #fc0;}\n")

        p._get_styles()

        output = p.run()
        desired = u"""<?xml version='1.0' encoding='utf-8'?>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
<title>test</title>


</head>
<body>
<h1 style="color: #fc0">Hello World!</h1>
<p style="color: #999">:)</p>
</body>
</html>"""
        self.assertEqual(output, desired)

    def test_overloaded_styles(self):
        html = '<style>h1 { color: red; } #test { color: blue; }</style>' \
               '<h1 id="test">Hello world!</h1>'
        expected = '<h1 id="test" style="color: blue">Hello world!</h1>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(expected, output)

    def test_unicode_content(self):
        html = u"""<h1>Hello World!</h1><p>\u2022 point</p>"""
        css = """h1 { color: red; }"""
        expected = u"""<h1 style="color: red">Hello World!</h1><p>\u2022 point</p>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)


class ExternalStyles(unittest.TestCase):
    def setUp(self):
        self.html_template = """<link rel="stylesheet" href="{href}"></link><span class="b1">Bold</span><span class="b2 c">Bold Red</span>"""
        self.root_url = 'http://server.com'
        self.relative_url = 'http://server.com/parent/child/'

    def _test_external_url(self, url, expected_url):
        with mock.patch.object(Pynliner, '_get_url') as mocked:
            def check_url(url):
                self.assertEqual(url, expected_url)
                return ".b1,.b2 { font-weight:bold; } .c {color: red}"
            mocked.side_effect = check_url
            p = Pynliner()
            p.root_url = self.root_url
            p.relative_url = self.relative_url
            p.from_string(self.html_template.format(href=url))
            p._get_soup()
            p._get_styles()

    def test_simple_url(self):
        self._test_external_url('test.css', 'http://server.com/parent/child/test.css')

    def test_relative_url(self):
        self._test_external_url('../test.css', 'http://server.com/parent/test.css')

    def test_absolute_url(self):
        self._test_external_url('/something/test.css', 'http://server.com/something/test.css')

    def test_external_url(self):
        self._test_external_url('http://other.com/something/test.css', 'http://other.com/something/test.css')

    def test_external_ssl_url(self):
        self._test_external_url('https://other.com/something/test.css', 'https://other.com/something/test.css')

    def test_external_schemeless_url(self):
        self._test_external_url('//other.com/something/test.css', 'http://other.com/something/test.css')


class CommaSelector(unittest.TestCase):
    def setUp(self):
        self.html = """<style>.b1,.b2 { font-weight:bold; } .c {color: red}</style><span class="b1">Bold</span><span class="b2 c">Bold Red</span>"""
        self.p = Pynliner().from_string(self.html)

    def test_fromString(self):
        """Test 'fromString' constructor"""
        self.assertEqual(self.p.source_string, self.html)

    def test_get_soup(self):
        """Test '_get_soup' method"""
        self.p._get_soup()
        self.assertEqual(unicode(self.p.soup), self.html)

    def test_get_styles(self):
        """Test '_get_styles' method"""
        self.p._get_soup()
        self.p._get_styles()
        self.assertEqual(self.p.style_string, u'.b1,.b2 { font-weight:bold; } .c {color: red}\n')
        self.assertEqual(unicode(self.p.soup), u'<span class="b1">Bold</span><span class="b2 c">Bold Red</span>')

    def test_apply_styles(self):
        """Test '_apply_styles' method"""
        self.p._get_soup()
        self.p._get_styles()
        self.p._apply_styles()
        self.assertEqual(unicode(self.p.soup), u'<span class="b1" style="font-weight: bold">Bold</span><span class="b2 c" style="font-weight: bold; color: red">Bold Red</span>')

    def test_run(self):
        """Test 'run' method"""
        output = self.p.run()
        self.assertEqual(output, u'<span class="b1" style="font-weight: bold">Bold</span><span class="b2 c" style="font-weight: bold; color: red">Bold Red</span>')

    def test_with_cssString(self):
        """Test 'with_cssString' method"""
        cssString = '.b1,.b2 {font-size: 2em;}'
        self.p = Pynliner().from_string(self.html).with_cssString(cssString)
        output = self.p.run()
        self.assertEqual(output, u'<span class="b1" style="font-weight: bold; font-size: 2em">Bold</span><span class="b2 c" style="font-weight: bold; color: red; font-size: 2em">Bold Red</span>')

    def test_fromString_complete(self):
        """Test 'fromString' complete"""
        output = pynliner.fromString(self.html)
        desired = u'<span class="b1" style="font-weight: bold">Bold</span><span class="b2 c" style="font-weight: bold; color: red">Bold Red</span>'
        self.assertEqual(output, desired)

    def test_comma_whitespace(self):
        """Test excess whitespace in CSS"""
        html = '<style>h1,  h2   ,h3,\nh4{   color:    #000}  </style><h1>1</h1><h2>2</h2><h3>3</h3><h4>4</h4>'
        desired_output = '<h1 style="color: #000">1</h1><h2 style="color: #000">2</h2><h3 style="color: #000">3</h3><h4 style="color: #000">4</h4>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)

    def test_comma_separated_nested_styles(self):
        html = """<style>.orange-wrapper p, .super-orange-wrapper p { color:orange; }</style><div class="orange-wrapper"><p>Orange</p></div><div><p>Black</p></div>"""
        desired_output = """<div class="orange-wrapper"><p style="color: orange">Orange</p></div><div><p>Black</p></div>"""
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)


class Extended(unittest.TestCase):
    def test_overwrite(self):
        """Test overwrite inline styles"""
        html = '<style>h1 {color: #000;}</style><h1 style="color: #fff">Foo</h1>'
        desired_output = '<h1 style="color: #000; color: #fff">Foo</h1>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)

    def test_overwrite_comma(self):
        """Test overwrite inline styles"""
        html = '<style>h1,h2,h3 {color: #000;}</style><h1 style="color: #fff">Foo</h1><h3 style="color: #fff">Foo</h3>'
        desired_output = '<h1 style="color: #000; color: #fff">Foo</h1><h3 style="color: #000; color: #fff">Foo</h3>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)


class MediaQuery(unittest.TestCase):
    def setUp(self):
        self.mq = '@media (min-width: 640px) { .infobox { float: right } }'

    def test_leave_alone(self):
        """Test media queries are 'left alone'"""
        html = '<style>' + self.mq + '</style>'\
               '<h1>Foo</h1><div class="infobox">Blah</div>'

        desired_output = '<style>' + self.mq + '</style>'\
            '<h1>Foo</h1><div class="infobox">Blah</div>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)

    def test_mixed_styles(self):
        """Test media queries do not affect regular operation"""
        html = '<style>' + self.mq + ' h1 {color:#ffcc00;}</style>'\
               '<h1>Foo</h1><div class="infobox">Blah</div>'

        desired_output = '<style>' + self.mq + '</style>'\
            '<h1 style="color: #fc0">Foo</h1><div class="infobox">Blah</div>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)

    def test_real_html(self):
        """Test re-inserted styles are placed in the body for HTML"""
        html = '<html><head><style>' + self.mq + ' h1 {color:#ffcc00;}</style></head>'\
               '<body><h1>Foo</h1><div class="infobox">Blah</div>'

        desired_output = '<html><head></head><body><style>' + self.mq + '</style>'\
            '<h1 style="color: #fc0">Foo</h1><div class="infobox">Blah</div>'\
            '</body></html>'
        output = Pynliner().from_string(html).run()
        self.assertEqual(output, desired_output)


class LogOptions(unittest.TestCase):
    def setUp(self):
        self.html = "<style>h1 { color:#ffcc00; }</style><h1>Hello World!</h1>"

    def test_no_log(self):
        self.p = Pynliner()
        self.assertEqual(self.p.log, None)
        self.assertEqual(cssutils.log.enabled, False)

    def test_custom_log(self):
        self.log = logging.getLogger('testlog')
        self.log.setLevel(logging.DEBUG)

        self.logstream = StringIO()
        handler = logging.StreamHandler(self.logstream)
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        formatter = logging.Formatter(log_format)
        handler.setFormatter(formatter)
        self.log.addHandler(handler)

        self.p = Pynliner(self.log).from_string(self.html)

        self.p.run()
        log_contents = self.logstream.getvalue()
        self.assertTrue("DEBUG" in log_contents)


class BeautifulSoupBugs(unittest.TestCase):
    def test_double_doctype(self):
        self.html = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN"
"http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">"""
        output = pynliner.fromString(self.html)
        self.assertTrue("<!<!" not in output)

    def test_double_comment(self):
        self.html = """<!-- comment -->"""
        output = pynliner.fromString(self.html)
        self.assertTrue("<!--<!--" not in output)


class Entities(unittest.TestCase):

    def test_html_entities_preserved_by_default(self):
        html = u'<p>&nbsp;</p>'
        output = pynliner.fromString(html)
        expected = html
        self.assertEqual(expected, output)

    def test_html_entities_preserved_explicitly(self):
        html = u'<p>&nbsp;</p>'
        output = pynliner.fromString(html, preserve_entities=True)
        expected = html
        self.assertEqual(expected, output)

    def test_html_entities_unpreserved_explicitly(self):
        html = u'<p>&nbsp;</p>'
        output = pynliner.fromString(html, preserve_entities=False)
        expected = u'<p>\xa0</p>'
        self.assertEqual(expected, output)


class ComplexSelectors(unittest.TestCase):

    def test_comma_specificity(self):
        html = '<i>howdy</i>'
        css = 'i, i { color: red; } i { color: blue; }'
        expected = '<i style="color: blue">howdy</i>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_missing_link_descendant_selector(self):
        html = '<div id="a"><i>x</i></div>'
        css = '#a b i { color: red }'
        expected = html
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_multiple_class_selector(self):
        html = """<h1 class="a b">Hello World!</h1>"""
        css = """h1.a.b { color: red; }"""
        expected = u'<h1 class="a b" style="color: red">Hello World!</h1>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_conflicting_multiple_class_selector(self):
        html = """<h1 class="a b">Hello World!</h1><h1 class="a">I should not be changed</h1>"""
        css = """h1.a.b { color: red; }"""
        expected = u'<h1 class="a b" style="color: red">Hello World!</h1><h1 class="a">I should not be changed</h1>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_combination_selector(self):
        html = """<h1 id="a" class="b">Hello World!</h1>"""
        css = """h1#a.b { color: red; }"""
        expected = u'<h1 class="b" id="a" style="color: red">Hello World!</h1>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_descendant_selector(self):
        html = """<h1><span>Hello World!</span></h1>"""
        css = """h1 span { color: red; }"""
        expected = u'<h1><span style="color: red">Hello World!</span></h1>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_selector(self):
        html = """<h1><span>Hello World!</span></h1>"""
        css = """h1 > span { color: red; }"""
        expected = u'<h1><span style="color: red">Hello World!</span></h1>'
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_nested_child_selector(self):
        html = """<div><h1><span>Hello World!</span></h1></div>"""
        css = """div > h1 > span { color: red; }"""
        expected = u"""<div><h1><span style="color: red">Hello World!</span></h1></div>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > span { color: red; }"""
        expected = u"""<h1><span style="color: red">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_all_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > * { color: red; }"""
        expected = u"""<h1><span style="color: red">Hello World!</span><p style="color: red">foo</p><div class="barclass" style="color: red"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_adjacent_selector(self):
        html = """<h1>Hello World!</h1><h2>How are you?</h2>"""
        css = """h1 + h2 { color: red; }"""
        expected = (u'<h1>Hello World!</h1>'
                    u'<h2 style="color: red">How are you?</h2>')
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_unknown_pseudo_selector(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > span:css4-selector { color: red; }"""
        expected = u"""<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_follow_by_adjacent_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > span + p { color: red; }"""
        expected = u"""<h1><span>Hello World!</span><p style="color: red">foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_follow_by_first_child_selector_with_white_spaces(self):
        html = """<h1> <span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > :first-child { color: red; }"""
        expected = u"""<h1> <span style="color: red">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_follow_by_first_child_selector_with_comments(self):
        html = """<h1> <!-- enough said --><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > :first-child { color: red; }"""
        expected = u"""<h1> <!-- enough said --><span style="color: red">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_follow_by_first_child_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > :first-child { color: red; }"""
        expected = u"""<h1><span style="color: red">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_last_child_selector(self):
        html = """<h1><span>Hello World!</span></h1>"""
        css = """h1 > :last-child { color: red; }"""
        expected = u"""<h1><span style="color: red">Hello World!</span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_multiple_pseudo_selectors(self):
        html = """<h1><span>Hello World!</span></h1>"""
        css = """span:first-child:last-child { color: red; }"""
        expected = u"""<h1><span style="color: red">Hello World!</span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)
        html = """<h1><span>Hello World!</span><span>again!</span></h1>"""
        css = """span:first-child:last-child { color: red; }"""
        expected = u"""<h1><span>Hello World!</span><span>again!</span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_parent_pseudo_selector(self):
        html = """<h1><span><span>Hello World!</span></span></h1>"""
        css = """span:last-child span { color: red; }"""
        expected = u"""<h1><span><span style="color: red">Hello World!</span></span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)
        html = """<h1><span><span>Hello World!</span></span></h1>"""
        css = """span:last-child > span { color: red; }"""
        expected = u"""<h1><span><span style="color: red">Hello World!</span></span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)
        html = """<h1><span><span>Hello World!</span></span><span>nope</span></h1>"""
        css = """span:last-child > span { color: red; }"""
        expected = u"""<h1><span><span>Hello World!</span></span><span>nope</span></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_follow_by_last_child_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > :last-child { color: red; }"""
        expected = u"""<h1><span>Hello World!</span><p>foo</p><div class="barclass" style="color: red"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_with_first_child_override_selector_complex_dom(self):
        html = """<div><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></div>"""
        css = """div > * { color: green; } div > :first-child { color: red; }"""
        expected = u"""<div><span style="color: red">Hello World!</span><p style="color: green">foo</p><div class="barclass" style="color: green"><span style="color: red">baz</span>bar</div></div>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_id_el_child_with_first_child_override_selector_complex_dom(self):
        html = """<div id="abc"><span class="cde">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></div>"""
        css = """#abc > * { color: green; } #abc > :first-child { color: red; }"""
        expected = u"""<div id="abc"><span class="cde" style="color: red">Hello World!</span><p style="color: green">foo</p><div class="barclass" style="color: green"><span>baz</span>bar</div></div>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_with_first_and_last_child_override_selector(self):
        html = """<p><span>Hello World!</span></p>"""
        css = """p > * { color: green; } p > :first-child:last-child { color: red; }"""
        expected = u"""<p><span style="color: red">Hello World!</span></p>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_nested_child_with_first_child_override_selector_complex_dom(self):
        self.maxDiff = None

        html = """<div><div><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></div></div>"""
        css = """div > div > * { color: green; } div > div > :first-child { color: red; }"""
        expected = u"""<div><div><span style="color: red">Hello World!</span><p style="color: green">foo</p><div class="barclass" style="color: green"><span style="color: red">baz</span>bar</div></div></div>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_with_first_child_and_class_selector_complex_dom(self):
        html = """<h1><span class="hello">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > .hello:first-child { color: green; }"""
        expected = u"""<h1><span class="hello" style="color: green">Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_child_with_first_child_and_unmatched_class_selector_complex_dom(self):
        html = """<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 > .hello:first-child { color: green; }"""
        expected = u"""<h1><span>Hello World!</span><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_first_child_descendant_selector(self):
        html = """<h1><div><span>Hello World!</span></div></h1>"""
        css = """h1 :first-child { color: red; }"""
        expected = u"""<h1><div style="color: red"><span style="color: red">Hello World!</span></div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_last_child_descendant_selector(self):
        html = """<h1><div><span>Hello World!</span></div></h1>"""
        css = """h1 :last-child { color: red; }"""
        expected = u"""<h1><div style="color: red"><span style="color: red">Hello World!</span></div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_first_child_descendant_selector_complex_dom(self):
        html = """<h1><div><span>Hello World!</span></div><p>foo</p><div class="barclass"><span>baz</span>bar</div></h1>"""
        css = """h1 :first-child { color: red; }"""
        expected = u"""<h1><div style="color: red"><span style="color: red">Hello World!</span></div><p>foo</p><div class="barclass"><span style="color: red">baz</span>bar</div></h1>"""
        output = Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(output, expected)

    def test_specificity(self):
        html = """<div class="foo"></div>"""
        css1 = """div,a,b,c,d,e,f,g,h,i,j { color: red; }"""
        css2 = """.foo { color: blue; }"""
        expected = u"""<div class="foo" style="color: blue"></div>"""
        output = pynliner.Pynliner().from_string(html).with_cssString(css1).with_cssString(css2).run()
        self.assertEqual(output, expected)


class AttributeSelectorTestCase(unittest.TestCase):

    def assert_pynlined(self, html, css, expected):
        actual = pynliner.Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(actual, expected)

    def test_exists(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)

    def test_equals(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type="thing"] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)
        css = '[data-type = "thing"] {color: red;}'
        self.assert_pynlined(html, css, expected)

    def test_one_of(self):
        html = '<span data-type="thing1 thing2">1</span>'
        css = '[data-type~="thing1"] {color: red;}'
        expected = u'<span data-type="thing1 thing2" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)
        css = '[data-type~="thing2"] {color: red;}'
        expected = u'<span data-type="thing1 thing2" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)

    def test_starts_with(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type^="th"] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)

    def test_ends_with(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type$="ng"] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)

    def test_contains(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type*="i"] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)

    def test_is_or_prefixed_by(self):
        html = '<span data-type="thing">1</span>'
        css = '[data-type|="thing"] {color: red;}'
        expected = u'<span data-type="thing" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)
        html = '<span data-type="thing-1">1</span>'
        expected = u'<span data-type="thing-1" style="color: red">1</span>'
        self.assert_pynlined(html, css, expected)


class IdenticalElementStringTest(unittest.TestCase):
    def test_identical_element(self):
        css = """
        .text-right {
            text-align: right;
        }
        .box {
            width:200px;
            border: 1px solid #000;
        }
        """
        html = """<div class="box"><p>Hello World</p><p class="text-right">Hello World on right</p><p class="text-right">Hello World on right</p></div>"""
        expected = """<div class="box" style="width: 200px; border: 1px solid #000"><p>Hello World</p><p class="text-right" style="text-align: right">Hello World on right</p><p class="text-right" style="text-align: right">Hello World on right</p></div>"""
        output = pynliner.Pynliner().from_string(html).with_cssString(css).run()
        self.assertEqual(expected, output)


if __name__ == '__main__':
    unittest.main()
