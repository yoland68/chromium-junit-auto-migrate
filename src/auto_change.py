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
    "chrome-base-test-case": chrome_convert_agents.ChromeActivityBaseCaseAgent,
    "chrome-permission-test": chrome_convert_agents.PermissionTestAgent,
    "chrome-tabbed-test": chrome_convert_agents.ChromeTabbedTestAgent,
    "instrumentation":
        instrumentation_convert_agents.InstrumentationTestCaseAgent,
    "base-class": test_base_convert_agent.BaseCaseAgent,
    "multiactivity-test": chrome_convert_agents.MultiActivityTestAgent,
    "vr-test": chrome_convert_agents.ChromeVrTestAgent,
    "payment-test": chrome_convert_agents.PaymentRequestAgent,
    "cast-test": chrome_convert_agents.CastTestAgent,
}

def ConvertDirectory(directory, java_parser, agent_strings,
                     save_as_new=False, logging_level=logging.WARNING,
                     use_base_class=False):
  agent = None
  for (dirpath, _, filenames) in os.walk(directory):
    for filename in filenames:
      whole_path = os.path.join(dirpath, filename)
      agent = ConvertFile(
          java_parser, agent_strings, whole_path, save_as_new,
          previous_agent=agent, logging_level=logging_level,
          use_base_class=use_base_class)

def ConvertFile(java_parser, agent_strings, whole_path, save_as_new,
                previous_agent=None, logging_level=logging.WARNING,
                use_base_class=False):
  logger = SetLogger(logging_level, whole_path)
  agent = previous_agent
  for agent_class in [_AGENT_DICT[i] for i in agent_strings if
                      _AGENT_DICT[i].filename_match(whole_path)]:
    agent = agent_class(java_parser, whole_path, logger=logger, agent=agent,
                        save_as_new=save_as_new, use_base_class=use_base_class)
    if use_base_class or not agent.skip():
      agent.actions()
      return agent

def SetLogger(logging_level, filepath):
  log = logging.getLogger()
  filename = filepath.split('/')[-1]
  f = logging.Formatter(
      filename + ':%(levelname)s:%(module)s:%(lineno)s: %(message)s')
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
  argument_parser.add_argument(
      '-u', '--use-base-class', help='Use another base class to convert',
      default=False, action='store_true')
  argument_parser.add_argument(
      '--no-skip', help='Do not skip the specified file', action='store_true',
      default=False)
  argument_parser.add_argument('-f', '--java-file', help='Java file')
  argument_parser.add_argument('-d', '--directory',
                               help='Directory where all java file lives')
  argument_parser.add_argument('-v', '--verbose', help='Log info',
                               action='store_true')
  argument_parser.add_argument(
      '-l', '--list-agents', help='List all available agents',
      action='store_true', default=False)
  argument_parser.add_argument('-n', '--save-as-new', default=False,
                               action='store_true', help='Save as a new file')
  argument_parser.add_argument(
      '-a', '--agent', help='Specify the agent for the current file',
      default='all')
  arguments = argument_parser.parse_args(sys.argv[1:])

  logging_level = logging.INFO
  if arguments.verbose:
    logging_level = logging.DEBUG

  if arguments.list_agents:
    print('Available agents and description:\n')
    for agent, agent_class in _AGENT_DICT.iteritems():
      print("%25s:\t%s" % (agent, agent_class.__doc__.strip()))
    return

  if arguments.java_file and arguments.directory:
    raise Exception(
        'Can not specify --jave-file and --directory at the same time')

  if arguments.agent == 'all':
    agents = _AGENT_DICT.keys()
  else:
    agents = [arguments.agent]
  java_parser = CreateJavaParser()
  if arguments.java_file:
    ConvertFile(java_parser, agents, arguments.java_file,
                arguments.save_as_new, logging_level=logging_level,
                use_base_class=arguments.use_base_class)
  else:
    ConvertDirectory(
        arguments.directory, java_parser, agents,
        save_as_new=arguments.save_as_new, logging_level=logging_level,
        use_base_class=arguments.use_base_class)

if __name__ == '__main__':
  main()

