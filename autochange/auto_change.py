#!/usr/bin/env python

import model
import parser
import base_agent
import chrome_convert_agents
import instrumentation_convert_agents
import test_base_convert_agent

import json
import re
import logging
import argparse
import os
import collections
import sys

import codecs

_AGENT_DICT = {
    "base": base_agent.BaseAgent,
    "chrome-base-test-case": chrome_convert_agents.ChromeActivityBaseCaseAgent,
    "chrome-permission-test": chrome_convert_agents.PermissionTestAgent,
    "chrome-tabbed-test": chrome_convert_agents.ChromeTabbedTestAgent,
    "instrumentation":
        instrumentation_convert_agents.InstrumentationTestCaseAgent,
    "base-class": test_base_convert_agent.BaseCaseAgent,
    "multiactivity-test": chrome_convert_agents.MultiActivityTestAgent,
    "temp": chrome_convert_agents.TempChromeBaseRefactorAgent,
}

def ConvertDirectory(directory, java_parser, agent_strings,
                     save_as_new=False, logging_level=logging.WARNING):
  agent = None
  for (dirpath, _, filenames) in os.walk(directory):
    for filename in filenames:
      whole_path = os.path.join(dirpath, filename)
      agent = ConvertFile(
          java_parser, agent_strings, whole_path, save_as_new,
          previous_agent=agent, logging_level=logging_level)

def ConvertFile(java_parser, agent_strings, whole_path, save_as_new,
                previous_agent=None, logging_level=logging.WARNING):
  logger = SetLogger(logging_level, whole_path)
  agent = previous_agent
  for agent_class in [_AGENT_DICT[i] for i in agent_strings if
                      _AGENT_DICT[i].filename_match(whole_path)]:
    agent = agent_class(java_parser, whole_path, logger=logger, agent=agent,
                        save_as_new=save_as_new)
    if not agent.skip():
      agent.actions()
      return agent

def SetLogger(logging_level, filepath):
  log = logging.getLogger()
  filename = filepath.split('/')[-1]
  f = logging.Formatter(filename + ':%(levelname)s:%(module)s:%(lineno)s: %(message)s')
  fh = logging.StreamHandler()
  fh.setLevel(logging_level)
  fh.setFormatter(f)
  log.propagate = False
  if len(log.handlers) > 0:
    log.removeHandler(log.handlers[0])
  log.setLevel(logging_level)
  log.addHandler(fh)
  return log

def CreateJavaParser(logging_level=logging.ERROR):
  logger = logging.getLogger('parser_logger')
  logger.setLevel(logging_level)
  return parser.Parser(logger)

def main():
  argument_parser = argparse.ArgumentParser()
  argument_parser.add_argument('-f', '--java-file', help='Java file')
  argument_parser.add_argument('-n', '--save-as-new', default=False,
                               action='store_true', help='Save as a new file')
  argument_parser.add_argument('-d', '--directory',
                               help='Directory where all java file lives')
  argument_parser.add_argument('-v', '--verbose', help='Log info',
                               action='store_true')
  argument_parser.add_argument('-s', '--skip', help='skip files')
  argument_parser.add_argument(
      '-m', '--mapping-file', dest='mapping_file',
      help='json file that maps all the TestBase to TestRule info')
  argument_parser.add_argument(
      '-a', '--agent', help='Specify the agent for the current file',
      default='all')
  arguments = argument_parser.parse_args(sys.argv[1:])

  if arguments.java_file and arguments.directory:
    raise Exception(
        'Can not specify --jave-file and --directory at the same time')

  logging_level = logging.WARNING
  if arguments.verbose:
    logging_level = logging.INFO
  if arguments.agent == 'all':
    agents = _AGENT_DICT.keys()
  else:
    agents = [arguments.agent]
  java_parser = CreateJavaParser()
  if arguments.java_file:
    ConvertFile(java_parser, agents, arguments.java_file,
                arguments.save_as_new, logging_level=logging_level)
  else:
    ConvertDirectory(
        arguments.directory, java_parser, agents,
        save_as_new=arguments.save_as_new, logging_level=logging_level)

if __name__ == '__main__':
  main()

