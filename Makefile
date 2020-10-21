.PHONY : install

install:
	pip install --user --upgrade .
	@echo "Pronto! 'cc201' instalado com sucesso."
	@echo "Agora você pode executá-lo com 'cc201 <arquivo-fonte>'"


clean:
	pip uninstall -y cc201 ply
