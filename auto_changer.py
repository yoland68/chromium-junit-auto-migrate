import plyj.parser as ply

def main():
  parser = ply.Parser()
  tree = parser.parse_file(file('content/public/android/javatests/src/org/chromium/content/browser/PopupZoomerTest.java'))
  import ipdb
  ipdb.set_trace()

main()
