import pkgutil
import chromadb.telemetry

print("Telemetry submodules:")
for submodule in pkgutil.walk_packages(chromadb.telemetry.__path__, chromadb.telemetry.__name__ + "."):
    print(submodule.name)
