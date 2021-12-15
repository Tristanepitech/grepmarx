# -*- encoding: utf-8 -*-
"""
Copyright (c) 2021 - present Orange Cyberdefense
"""

import os
import re
from glob import glob
from datetime import datetime
from shutil import rmtree

import git
from flask import current_app
from grepmarx import db
from grepmarx.constants import (
    RULE_EXTENSIONS,
    RULES_PATH,
    SEVERITY_LOW,
    SEVERITY_MEDIUM,
    TOP40_CWE_SEVERITIES,
)
from grepmarx.rules.models import Rule, RuleRepository, SupportedLanguage
from yaml import YAMLError, safe_load

##
## Rule utils
##


def sync_db(rules_folder):
    """Parse all libsast/semgrep YAML rule files in the given folder, and for each
    rule create new a Rule object and persist it in the database. Existing rules ID
    are kept to preserve rule packs consistency.

    Args:
        rules_folder (str): path of the folder containing libsast/semgrep YAML rule files
    """
    # Get all YML files in the folder
    rules_filenames = list()
    for c_ext in RULE_EXTENSIONS:
        rules_filenames += glob(
            pathname=os.path.join(rules_folder, "**", "*" + c_ext), recursive=True
        )
    supported_languages = SupportedLanguage.query.all()
    # Parse rules in these files
    for c_filename in rules_filenames:
        with open(c_filename, "r") as yml_stream:
            try:
                yml_rules = safe_load(yml_stream)
                file_path = c_filename.replace(RULES_PATH, "")
                repository = file_path.split(os.path.sep)[0]
                category = ".".join(file_path.split(os.path.sep)[1:][:-1])
                # Extract rules from the file, if any
                if "rules" in yml_rules:
                    for c_rule in yml_rules["rules"]:
                        rule = Rule.query.filter_by(file_path=file_path).first()
                        # Create a new rule only if the file doesn't corresponds to an existing
                        # rule, in order to keep ids and not break RulePacks
                        if rule is None:
                            rule = Rule(
                                title=c_rule["id"],
                                file_path=file_path,
                                repository=RuleRepository.query.filter_by(
                                    name=repository
                                ).first(),
                                category=category,
                            )
                            db.session.add(rule)
                        # Associate the rule with a known, supported language
                        if "languages" in c_rule:
                            for c_language in c_rule["languages"]:
                                for c_sl in supported_languages:
                                    if c_sl.name.lower() == c_language.lower():
                                        rule.languages.append(c_sl)
                        # Add metadata: OWASP and CWE ids
                        if "metadata" in c_rule:
                            if "cwe" in c_rule["metadata"]:
                                rule.cwe = c_rule["metadata"]["cwe"]
                            if "owasp" in c_rule["metadata"]:
                                # There may be multiple OWASP ids (eg. 2017, 2021...)
                                if type(c_rule["metadata"]["owasp"]) is list:
                                    rule.owasp = c_rule["metadata"]["owasp"][0]
                                else:
                                    rule.owasp = c_rule["metadata"]["owasp"]
                        # Replace rule level/severity by a calculated one
                        rule.severity = generate_severity(rule.cwe)
                        current_app.logger.debug(
                            "Rule imported in DB: %s",
                            rule.repository.name
                            + "/"
                            + rule.category
                            + "/"
                            + rule.title,
                        )
            except YAMLError as e:
                db.session.rollback()
                raise (e)
            else:
                db.session.commit()


def generate_severity(cwe_string):
    """Generates a severity level from a CWE full name.

    For Top 40 CWE, the severity is an average of the CVSS scores
    for CVEs corresponding to this CWE. For CWE outside of the
    Top 40, the severity is MEDIUM by default. If no CWE is set,
    the severity is then LOW.

    Args:
        cwe_string (str): CWE full name (such as 'CWE-200: Exposure of
        Sensitive Information to an Unauthorized Actor')

    Returns:
        int: severity level (1-3)
    """
    ret = SEVERITY_LOW
    if cwe_string is not None:
        match = re.search("(CWE-\d+)", cwe_string, re.IGNORECASE)
        if match:
            cwe_id = match.group(1).upper()
            if cwe_id in TOP40_CWE_SEVERITIES:
                ret = TOP40_CWE_SEVERITIES[cwe_id]
            else:
                ret = SEVERITY_MEDIUM
    return ret


##
## RulePack utils
##


def validate_languages_rules(form):
    """Check that the 'languages' and 'rules' fields of a rule pack form are valid.

    Args:
        form (dict): form to validate (request.form)

    Returns:
        str: None if the fields are valid, a short error message otherwise
    """
    err = None
    # Need at least one language
    if len(form.languages.data) <= 0:
        err = "Please define at least one associated language for the rule pack"
    # Check the given rule list (comma separated integers)
    if not re.search("(\d+,)*\d+", form.rules.data, re.IGNORECASE):
        err = "Please define at least one rule for the rule pack"
    return err


def comma_separated_to_list(comma_separated):
    """Convert a string of comma separated IDs to a list of integers.
    Empty and duplicated elements are omitted.

    Args:
        comma_separated (str): string of comma separated IDs

    Returns:
        list: a list of integers
    """
    # Split the string into a list, then remove empty and duplicate elements
    r_list = list(dict.fromkeys(filter(None, comma_separated.split(","))))
    # Convert elements to integers
    for i in range(0, len(r_list)):
        r_list[i] = int(r_list[i])
    return r_list


##
## RuleRepository utils
##


def clone_rule_repo(repo):
    """Perform a 'clone' operation on the rule repository.
    The rule repository's 'last_update_on' attribute will be updated.

    Args:
        repo (RuleRepository): rule repository to clone
    """
    repo_path = os.path.join(RULES_PATH, repo.name)
    git.Repo.clone_from(repo.uri, repo_path)
    repo.last_update_on = datetime.now()
    db.session.commit()


def pull_rule_repo(repo):
    """Perform a 'pull' operation on the rule repository.
    The rule repository's 'last_update_on' attribute will be updated.

    Args:
        repo (RuleRepository): rule repository to pull
    """
    repo_path = os.path.join(RULES_PATH, repo.name)
    git.cmd.Git(repo_path).pull()
    repo.last_update_on = datetime.now()
    db.session.commit()


def remove_rule_repo(repo):
    """Delete the rule repository from the database (along with all its
    associated rules), and remove its folder from disk.

    Args:
        repo (RuleRepository): rule repository to remove
    """
    # Remove repository folder on disk
    repo_path = os.path.join(RULES_PATH, repo.name)
    if os.path.isdir(repo_path):
        rmtree(repo_path)
    db.session.delete(repo)
    db.session.commit()
