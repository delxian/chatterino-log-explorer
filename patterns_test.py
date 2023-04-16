"""Test cases."""
import unittest

from patterns import check_msg


class TestCheckMsg(unittest.TestCase):
    """something"""
    def test_check_msg_modes(self):
        """something"""
        self.assertTrue(
            check_msg("TEST MESSAGE","`U","",False,False))
        self.assertFalse(
            check_msg("TEST MESSAGe","`U","",False,False))
        self.assertTrue(
            check_msg("test message","`L","",False,False))
        self.assertFalse(
            check_msg("test messagE","`L","",False,False))
        self.assertTrue(
            check_msg("Test Message","`T","",False,False))
        self.assertFalse(
            check_msg("test Message","`T","",False,False))
        self.assertTrue(
            check_msg("Test message","`Ts","",False,False))
        self.assertFalse(
            check_msg("Test messagE","`Ts","",False,False))
        self.assertTrue(
            check_msg("!test message","`C","",False,False))
        self.assertFalse(
            check_msg("test message","`C","",False,False))

    def test_check_msg_sw(self):
        """something"""
        self.assertTrue(
            check_msg("alphabravo charlie deltaecho",">alpha","alpha",False,False))
        self.assertFalse(
            check_msg("alphbravo charlie deltaecho",">alpha","alpha",False,False))
        self.assertTrue(
            check_msg("alpha bravo charlie deltaecho",">alpha","alpha",False,True))
        self.assertFalse(
            check_msg("alphabravo charlie deltaecho",">alpha","alpha",False,True))
        self.assertTrue(
            check_msg("alphabravo charlie deltaecho",">alpha","alpha",True,False))
        self.assertFalse(
            check_msg("Alphabravo charlie deltaecho",">alpha","alpha",True,False))
        self.assertTrue(
            check_msg("alpha bravo charlie deltaecho",">alpha","alpha",True,True))
        self.assertFalse(
            check_msg("Alpha bravo charlie deltaecho",">alpha","alpha",True,True))

    def test_check_msg_ew(self):
        """something"""
        self.assertTrue(
            check_msg("alphabravo charlie deltaecho","echo<","echo",False,False))
        self.assertFalse(
            check_msg("alphabravo charlie deltacho","echo<","echo",False,False))
        self.assertTrue(
            check_msg("alphabravo charlie delta echo","echo<","echo",False,True))
        self.assertFalse(
            check_msg("alphabravo charlie deltaecho","echo<","echo",False,True))
        self.assertTrue(
            check_msg("alphabravo charlie deltaecho","echo<","echo",True,False))
        self.assertFalse(
            check_msg("alphabravo charlie deltaEcho","echo<","echo",True,False))
        self.assertTrue(
            check_msg("alphabravo charlie delta echo","echo<","echo",True,True))
        self.assertFalse(
            check_msg("alphabravo charlie delta Echo","echo<","echo",True,True))

    def test_check_msg_ex(self):
        """something"""
        self.assertTrue(
            check_msg("alpha bravo charli delta echo","~charlie","charlie",False,False))
        self.assertFalse(
            check_msg("alpha bravo charlie delta echo","~charlie","charlie",False,False))
        self.assertTrue(
            check_msg("alpha bravocharlie delta echo","~charlie","charlie",False,True))
        self.assertFalse(
            check_msg("alpha bravo charlie delta echo","~charlie","charlie",False,True))
        self.assertTrue(
            check_msg("alpha bravo Charlie delta echo","~charlie","charlie",True,False))
        self.assertFalse(
            check_msg("alpha bravo charlie delta echo","~charlie","charlie",True,False))
        self.assertTrue(
            check_msg("alpha bravoCharlie delta echo","~charlie","charlie",True,True))
        self.assertFalse(
            check_msg("alpha bravo charlie delta echo","~charlie","charlie",True,True))

    def test_check_msg_inc(self):
        """something"""
        self.assertTrue(
            check_msg("alpha bravo charlie delta echo","charlie","charlie",False,False))
        self.assertFalse(
            check_msg("alpha bravo charli delta echo","charlie","charlie",False,False))
        self.assertTrue(
            check_msg("alpha bravo charlie delta echo","charlie","charlie",False,True))
        self.assertFalse(
            check_msg("alpha bravocharlie delta echo","charlie","charlie",False,True))
        self.assertTrue(
            check_msg("alpha bravo charlie delta echo","charlie","charlie",True,False))
        self.assertFalse(
            check_msg("alpha bravo Charlie delta echo","charlie","charlie",True,False))
        self.assertTrue(
            check_msg("alpha bravo charlie delta echo","charlie","charlie",True,True))
        self.assertFalse(
            check_msg("alpha bravo Charlie delta echo","charlie","charlie",True,True))
