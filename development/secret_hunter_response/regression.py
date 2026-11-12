"""Run inherited official-engine fixtures under the new ledger, not the old budget."""
import json,unittest
from development.secret_hunter_program.common import ROOT,write
from development.secret_hunter_response.accounting import reserve,finish
from development.secret_hunter_tactics import checks as c
name='regression-'+c.CANDIDATE.name;reserve(name,short=1500,full=15,seconds=300)
r=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(c.Mechanisms))
report={'tests':r.testsRun,'failures':len(r.failures),'errors':len(r.errors),'fixtures':c.FIXTURES,'evidence':c.EVIDENCE}
write(ROOT/c.ARGS.out,report);finish(name,actual_short=c.FIXTURES,tests_passed=r.wasSuccessful());assert r.wasSuccessful()
